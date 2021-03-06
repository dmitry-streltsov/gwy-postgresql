import unittest
from unittest.mock import patch, call, Mock

import numpy as np

from pygwyfile._libgwyfile import ffi
from pygwyfile.gwyfile import GwyfileErrorCMsg
from pygwyfile.gwygraph import GwyGraphCurve, GwyGraphModel


class GwyGraphModel_init(unittest.TestCase):
    """Test constructor of GwyGraphModel class
    """

    def setUp(self):
        self.test_meta = {'ncurves': 2,
                          'title': 'Plot',
                          'top_label': 'Top label',
                          'left_label': 'Left label',
                          'right_label': 'Right label',
                          'bottom_label': 'Bottom label',
                          'x_unit': 'm',
                          'y_unit': 'm',
                          'x_min': 0.,
                          'x_min_set': True,
                          'x_max': 1.,
                          'x_max_set': True,
                          'y_min': None,
                          'y_min_set': False,
                          'y_max': None,
                          'y_max_set': False,
                          'x_is_logarithmic': False,
                          'y_is_logarithmic': False,
                          'label.visible': True,
                          'label.has_frame': True,
                          'label.reverse': False,
                          'label.frame_thickness': 1,
                          'label.position': 0,
                          'grid-type': 1}
        self.test_curves = [Mock(spec=GwyGraphCurve),
                            Mock(spec=GwyGraphCurve)]

    def test_init_with_curves_and_meta(self):
        """Test GwyGraphModel constructor if meta is defined
        """
        graph = GwyGraphModel(curves=self.test_curves,
                              meta=self.test_meta)
        self.assertEqual(graph.curves, self.test_curves)
        self.assertDictEqual(graph.meta, self.test_meta)

    def test_init_with_curves_without_meta(self):
        """Test GwyGraphModel constructor with default meta
        """
        graph = GwyGraphModel(curves=self.test_curves)
        self.assertEqual(graph.curves, self.test_curves)
        self.assertDictEqual(graph.meta,
                             {'ncurves': 2,
                              'title': '',
                              'top_label': '',
                              'left_label': '',
                              'right_label': '',
                              'bottom_label': '',
                              'x_unit': '',
                              'y_unit': '',
                              'x_min': None,
                              'x_min_set': False,
                              'x_max': None,
                              'x_max_set': False,
                              'y_min': None,
                              'y_min_set': False,
                              'y_max': None,
                              'y_max_set': False,
                              'x_is_logarithmic': False,
                              'y_is_logarithmic': False,
                              'label.visible': True,
                              'label.has_frame': True,
                              'label.reverse': False,
                              'label.frame_thickness': 1,
                              'label.position': 0,
                              'grid-type': 1})

    def test_raise_TypeError_if_curve_is_not_GwyGraphCurve(self):
        """Raise TypeError exception if curve is not GwyGraphCurve
        instance
        """
        self.assertRaises(TypeError,
                          GwyGraphModel,
                          curves=np.random.rand(10))

    def test_raise_ValueError_if_curves_number_and_ncurves_different(self):
        """Raise ValueError if len(curves) is not equal to meta['ncurves']
        """
        self.assertRaises(ValueError,
                          GwyGraphModel,
                          curves=[Mock(GwyGraphCurve)],  # just one curve
                          meta=self.test_meta)           # meta['ncurves'] = 2


class GwyGraphModel_from_gwy(unittest.TestCase):
    """Test from_gwy method of GwyGraphModel class
    """

    @patch('pygwyfile.gwygraph.GwyGraphModel', autospec=True)
    @patch('pygwyfile.gwygraph.GwyGraphCurve', autospec=True)
    @patch.object(GwyGraphModel, '_get_curves')
    @patch.object(GwyGraphModel, '_get_meta')
    def test_arg_passing_to_other_methods(self,
                                          mock_get_meta,
                                          mock_get_curves,
                                          mock_GwyGraphCurve,
                                          mock_GwyGraphModel):
        """
        """
        gwygraphmodel = Mock()
        test_meta = {'ncurves': 2}
        test_gwycurves = [Mock(), Mock()]
        mock_get_meta.return_value = test_meta
        mock_get_curves.return_value = test_gwycurves
        graphmodel = Mock(spec=GwyGraphModel)
        mock_GwyGraphModel.return_value = graphmodel

        graph = GwyGraphModel.from_gwy(gwygraphmodel)

        # get meta data from <GwyGraphModel*> object
        mock_get_meta.assert_has_calls(
            [call(gwygraphmodel)])

        # get list of <GwyGraphModelCurve*> objects
        mock_get_curves.assert_has_calls(
            [call(gwygraphmodel, test_meta['ncurves'])])

        # create list of GwyGraphCurves instances
        mock_GwyGraphCurve.from_gwy.assert_has_calls(
            [call(gwycurve) for gwycurve in test_gwycurves])

        # create GwyGraphModel instance
        mock_GwyGraphModel.assert_has_calls(
            [call(curves=[mock_GwyGraphCurve.from_gwy.return_value
                          for gwycurve in test_gwycurves],
                  meta=test_meta)])

        # return GwyGraphModel instance
        self.assertEqual(graph, graphmodel)


class GwyGraphModel_get_meta(unittest.TestCase):
    """Test _get_meta method of GwyGraphModel class
    """

    def setUp(self):
        self.gwygraphmodel = Mock()

        patcher_lib = patch('pygwyfile.gwygraph.lib',
                            autospec=True)
        self.addCleanup(patcher_lib.stop)
        self.mock_lib = patcher_lib.start()

    def test_getting_number_of_curves(self):
        """
        Test getting number of curves from graphmodel object
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._get_number_of_curves)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['ncurves'], 3)

    def _get_number_of_curves(self, *args):
        """
        Return 3 as a number of curves in graphmodel object
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['ncurves'][0] = 3

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_title_field_is_not_empty(self):
        """
        'title' field in graphmodel object is not empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._title_is_not_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['title'], "test title")

    def _title_is_not_empty(self, *args):
        """
        Write "test title" C string to title field
        """

        title = ffi.new("char[]", b"test title")

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['title'][0] = title

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_title_field_is_empty(self):
        """
        'title' field in graphmodel object is empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._title_is_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['title'], '')

    def _title_is_empty(self, *args):
        """
        Write NULL to title field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['title'][0] = ffi.NULL

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_top_label_field_is_not_empty(self):
        """
        'top_label' field in graphmodel object is not empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._top_label_is_not_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['top_label'], "test top label")

    def _top_label_is_not_empty(self, *args):
        """
        Write "test top label" C string to 'top_label' field
        """

        top_label = ffi.new("char[]", b"test top label")

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['top_label'][0] = top_label

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_top_label_field_is_empty(self):
        """
        'top_label' field in graphmodel object is empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._top_label_is_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['top_label'], '')

    def _top_label_is_empty(self, *args):
        """
        Write NULL to top_label field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['top_label'][0] = ffi.NULL

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_left_label_field_is_not_empty(self):
        """
        'left_label' field in graphmodel object is not empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._left_label_is_not_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['left_label'], "test left label")

    def _left_label_is_not_empty(self, *args):
        """
        Write "test left label" C string to 'left_label' field
        """

        left_label = ffi.new("char[]", b"test left label")

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['left_label'][0] = left_label

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_left_label_field_is_empty(self):
        """
        'left_label' field in graphmodel object is empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._left_label_is_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['left_label'], '')

    def _left_label_is_empty(self, *args):
        """
        Write NULL to left_label field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['left_label'][0] = ffi.NULL

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_right_label_field_is_not_empty(self):
        """
        'right_label' field in graphmodel object is not empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._right_label_is_not_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['right_label'], "test right label")

    def _right_label_is_not_empty(self, *args):
        """
        Write "test right label" C string to 'right_label' field
        """

        right_label = ffi.new("char[]", b"test right label")

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['right_label'][0] = right_label

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_right_label_field_is_empty(self):
        """
        'right_label' field in graphmodel object is empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._right_label_is_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['right_label'], '')

    def _right_label_is_empty(self, *args):
        """
        Write NULL to right_label field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['right_label'][0] = ffi.NULL

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_bottom_label_field_is_not_empty(self):
        """
        'bottom_label' field in graphmodel object is not empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._bottom_label_is_not_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['bottom_label'], "test bottom label")

    def _bottom_label_is_not_empty(self, *args):
        """
        Write "test bottom label" C string to 'bottom_label' field
        """

        bottom_label = ffi.new("char[]", b"test bottom label")

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['bottom_label'][0] = bottom_label

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_bottom_label_field_is_empty(self):
        """
        'bottom_label' field in graphmodel object is empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._bottom_label_is_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['bottom_label'], '')

    def _bottom_label_is_empty(self, *args):
        """
        Write NULL to bottom_label field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['bottom_label'][0] = ffi.NULL

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_x_unit_field_is_not_empty(self):
        """
        'x_unit' field in graphmodel object is not empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._x_unit_is_not_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['x_unit'], 'm')

    def _x_unit_is_not_empty(self, *args):
        """
        Write "m" C string to 'x_unit' field
        """

        x_unit = ffi.new("char[]", b"m")

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['x_unit'][0] = x_unit

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_x_unit_field_is_empty(self):
        """
        'x_unit' field in graphmodel object is empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._x_unit_is_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['x_unit'], '')

    def _x_unit_is_empty(self, *args):
        """
        Write NULL to x_unit field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['x_unit'][0] = ffi.NULL

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_y_unit_field_is_not_empty(self):
        """
        'y_unit' field in graphmodel object is not empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._y_unit_is_not_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['y_unit'], 'm')

    def _y_unit_is_not_empty(self, *args):
        """
        Write "m" C string to 'y_unit' field
        """

        y_unit = ffi.new("char[]", b"m")

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['y_unit'][0] = y_unit

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_y_unit_field_is_empty(self):
        """
        'y_unit' field in graphmodel object is empty
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._y_unit_is_empty)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['y_unit'], '')

    def _y_unit_is_empty(self, *args):
        """
        Write NULL to y_unit field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['y_unit'][0] = ffi.NULL

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_x_min_set_is_true(self):
        """
        Check metadata dictionary if 'x_min_set' is True
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._x_min_set_is_true)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['x_min_set'], True)
        self.assertEqual(meta['x_min'], 0.)

    def _x_min_set_is_true(self, *args):
        """
        Write True in 'x_min_set' field and 0. in 'x_min' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        truep = ffi.new("bool*", True)

        arg_dict['x_min_set'][0] = truep[0]
        arg_dict['x_min'][0] = 0.

        # C func returns true if the graphmodel object loock acceptable
        return truep[0]

    def test_x_min_set_is_false(self):
        """
        Check metadata dictionary if 'x_min_set' is False
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._x_min_set_is_false)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['x_min_set'], False)
        self.assertIsNone(meta['x_min'])

    def _x_min_set_is_false(self, *args):
        """
        Write False in 'x_min_set' field and 0. in 'x_min' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        truep = ffi.new("bool*", True)
        falsep = ffi.new("bool*", False)

        arg_dict['x_min_set'][0] = falsep[0]
        arg_dict['x_min'][0] = 0.

        # C func returns true if the graphmodel object loock acceptable
        return truep[0]

    def test_x_max_set_is_true(self):
        """
        Check metadata dictionary if 'x_max_set' is True
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._x_max_set_is_true)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['x_max_set'], True)
        self.assertEqual(meta['x_max'], 0.)

    def _x_max_set_is_true(self, *args):
        """
        Write True in 'x_max_set' field and 0. in 'x_max' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        truep = ffi.new("bool*", True)

        arg_dict['x_max_set'][0] = truep[0]
        arg_dict['x_max'][0] = 0.

        # C func returns true if the graphmodel object loock acceptable
        return truep[0]

    def test_x_max_set_is_false(self):
        """
        Check metadata dictionary if 'x_max_set' is False
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._x_max_set_is_false)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['x_max_set'], False)
        self.assertIsNone(meta['x_max'])

    def _x_max_set_is_false(self, *args):
        """
        Write False in 'x_max_set' field and 0. in 'x_max' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        truep = ffi.new("bool*", True)
        falsep = ffi.new("bool*", False)

        arg_dict['x_max_set'][0] = falsep[0]
        arg_dict['x_max'][0] = 0.

        # C func returns true if the graphmodel object loock acceptable
        return truep[0]

    def test_y_min_set_is_true(self):
        """
        Check metadata dictionary if 'y_min_set' is True
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._y_min_set_is_true)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['y_min_set'], True)
        self.assertEqual(meta['y_min'], 0.)

    def _y_min_set_is_true(self, *args):
        """
        Write True in 'y_min_set' field and 0. in 'y_min' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        truep = ffi.new("bool*", True)

        arg_dict['y_min_set'][0] = truep[0]
        arg_dict['y_min'][0] = 0.

        # C func returns true if the graphmodel object loock acceptable
        return truep[0]

    def test_y_min_set_is_false(self):
        """
        Check metadata dictionary if 'y_min_set' is False
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._y_min_set_is_false)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['y_min_set'], False)
        self.assertIsNone(meta['y_min'])

    def _y_min_set_is_false(self, *args):
        """
        Write False in 'y_min_set' field and 0. in 'y_min' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        truep = ffi.new("bool*", True)
        falsep = ffi.new("bool*", False)

        arg_dict['y_min_set'][0] = falsep[0]
        arg_dict['y_min'][0] = 0.

        # C func returns true if the graphmodel object loock acceptable
        return truep[0]

    def test_y_max_set_is_true(self):
        """
        Check metadata dictionary if 'y_max_set' is True
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._y_max_set_is_true)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['y_max_set'], True)
        self.assertEqual(meta['y_max'], 0.)

    def _y_max_set_is_true(self, *args):
        """
        Write True in 'y_max_set' field and 0. in 'y_max' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        truep = ffi.new("bool*", True)

        arg_dict['y_max_set'][0] = truep[0]
        arg_dict['y_max'][0] = 0.

        # C func returns true if the graphmodel object loock acceptable
        return truep[0]

    def test_y_max_set_is_false(self):
        """
        Check metadata dictionary if 'y_max_set' is False
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._y_max_set_is_false)
        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['y_max_set'], False)
        self.assertIsNone(meta['y_max'])

    def _y_max_set_is_false(self, *args):
        """
        Write False in 'y_max_set' field and 0. in 'y_max' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        truep = ffi.new("bool*", True)
        falsep = ffi.new("bool*", False)

        arg_dict['y_max_set'][0] = falsep[0]
        arg_dict['y_max'][0] = 0.

        # C func returns true if the graphmodel object loock acceptable
        return truep[0]

    def test_x_is_logarithmic_true(self):
        """
        'x_is_logarithmic' field is True
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._x_is_logarithmic)

        self.x_is_logarithmic = True

        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['x_is_logarithmic'], True)

    def test_x_is_logarithmic_false(self):
        """
        'x_is_logarithmic' field is False
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._x_is_logarithmic)

        self.x_is_logarithmic = False

        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['x_is_logarithmic'], False)

    def _x_is_logarithmic(self, *args):
        """
        Write self.x_is_logarithmic in 'x_is_logarithmic' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        truep = ffi.new("bool*", True)
        falsep = ffi.new("bool*", False)

        if self.x_is_logarithmic:
            arg_dict['x_is_logarithmic'][0] = truep[0]
        else:
            arg_dict['x_is_logarithmic'][0] = falsep[0]

        # C func returns true if the graphmodel object loock acceptable
        return truep[0]

    def test_y_is_logarithmic_true(self):
        """
        'y_is_logarithmic' field is True
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._y_is_logarithmic)

        self.y_is_logarithmic = True

        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['y_is_logarithmic'], True)

    def test_y_is_logarithmic_false(self):
        """
        'y_is_logarithmic' field is False
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._y_is_logarithmic)

        self.y_is_logarithmic = False

        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['y_is_logarithmic'], False)

    def _y_is_logarithmic(self, *args):
        """
        Write self.y_is_logarithmic in 'y_is_logarithmic' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        truep = ffi.new("bool*", True)
        falsep = ffi.new("bool*", False)

        if self.y_is_logarithmic:
            arg_dict['y_is_logarithmic'][0] = truep[0]
        else:
            arg_dict['y_is_logarithmic'][0] = falsep[0]

        # C func returns true if the graphmodel object loock acceptable
        return truep[0]

    def test_label_visible_is_true(self):
        """
        'label.visible' field is True
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._label_visible)

        self.label_visible = True

        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['label.visible'], True)

    def test_label_visible_is_false(self):
        """
        'label.visible' field is False
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._label_visible)

        self.label_visible = False

        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['label.visible'], False)

    def _label_visible(self, *args):
        """
        Write self.label_visible in 'label.visible' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        truep = ffi.new("bool*", True)
        falsep = ffi.new("bool*", False)

        if self.label_visible:
            arg_dict['label.visible'][0] = truep[0]
        else:
            arg_dict['label.visible'][0] = falsep[0]

        # C func returns true if the graphmodel object loock acceptable
        return truep[0]

    def test_label_has_frame_is_true(self):
        """
        'label.has_frame' field is True
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._label_has_frame)

        self.label_has_frame = True

        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['label.has_frame'], True)

    def test_label_has_frame_is_false(self):
        """
        'label.has_frame' field is False
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._label_has_frame)

        self.label_has_frame = False

        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['label.has_frame'], False)

    def _label_has_frame(self, *args):
        """
        Write self.label_has_frame in 'label.has_frame' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        truep = ffi.new("bool*", True)
        falsep = ffi.new("bool*", False)

        if self.label_has_frame:
            arg_dict['label.has_frame'][0] = truep[0]
        else:
            arg_dict['label.has_frame'][0] = falsep[0]

        # C func returns true if the graphmodel object loock acceptable
        return truep[0]

    def test_label_reverse_is_true(self):
        """
        'label.reverse' field is True
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._label_reverse)

        self.label_reverse = True

        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['label.reverse'], True)

    def test_label_reverse_is_false(self):
        """
        'label.reverse' field is False
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._label_reverse)

        self.label_reverse = False

        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertIs(meta['label.reverse'], False)

    def _label_reverse(self, *args):
        """
        Write self.label_reverse in 'label.reverse' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        truep = ffi.new("bool*", True)
        falsep = ffi.new("bool*", False)

        if self.label_reverse:
            arg_dict['label.reverse'][0] = truep[0]
        else:
            arg_dict['label.reverse'][0] = falsep[0]

        # C func returns true if the graphmodel object loock acceptable
        return truep[0]

    def test_label_frame_thickness(self):
        """
        Check 'label.frame_thickness' field in metadata dictionary
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._label_frame_thickness)

        self.label_frame_thickness = 1

        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['label.frame_thickness'],
                         self.label_frame_thickness)

    def _label_frame_thickness(self, *args):
        """
        Write self.label_frame_thickness in 'label.frame_thickness' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['label.frame_thickness'][0] = self.label_frame_thickness
        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_label_position(self):
        """
        Check 'label.position' field in metadata dictionary
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._label_position)

        self.label_position = 1

        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['label.position'], self.label_position)

    def _label_position(self, *args):
        """
        Write self.label_position in 'label.position' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['label.position'][0] = self.label_position
        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_grid_type(self):
        """
        Check 'grid-type' field in metadata dictionary
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._grid_type)

        self.grid_type = 1

        meta = GwyGraphModel._get_meta(self.gwygraphmodel)
        self.assertEqual(meta['grid-type'], self.grid_type)

    def _grid_type(self, *args):
        """
        Write self.grid_type in 'grid-type' field
        """

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['grid-type'][0] = self.grid_type

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]

    def test_raise_exception_if_graphmodel_object_looks_unacceptable(self):
        """
        Raise GwyfileErrorCMsg if gwyfile_object_graphmodel_get returns False
        """

        falsep = ffi.new("bool*", False)
        self.mock_lib.gwyfile_object_graphmodel_get.return_value = (
            falsep[0])
        self.assertRaises(GwyfileErrorCMsg,
                          GwyGraphModel.from_gwy,
                          self.gwygraphmodel)


class GwyGraphModel_get_curves(unittest.TestCase):
    """
    Test _get_curves method of GwyGraphModel class
    """

    def setUp(self):
        self.ncurves = 3   # number of curves in graphmodel object
        self.curves_array = ffi.new("GwyfileObject*[]", self.ncurves)
        self.gwygraphmodel = Mock()

        patcher_lib = patch('pygwyfile.gwygraph.lib',
                            autospec=True)
        self.addCleanup(patcher_lib.stop)
        self.mock_lib = patcher_lib.start()

    def test_raise_exception_if_graphmodel_object_looks_unacceptable(self):
        """
        Raise GwyfileErrorCMsg if gwyfile_object_graphmodel_get returns False
        """

        falsep = ffi.new("bool*", False)
        self.mock_lib.gwyfile_object_graphmodel_get.return_value = falsep[0]
        self.assertRaises(GwyfileErrorCMsg,
                          GwyGraphModel._get_curves,
                          self.gwygraphmodel,
                          self.ncurves)

    def test_get_curves_array(self):
        """
        Get array of curves (GwyfileObjects) from graphmodel object
        """

        self.mock_lib.gwyfile_object_graphmodel_get.side_effect = (
            self._side_effect)
        curves = GwyGraphModel._get_curves(self.gwygraphmodel,
                                           self.ncurves)
        self.assertListEqual(curves, list(self.curves_array))

    def _side_effect(self, *args):
        """
        Check args of gwyfile_object_graphmodel_get func
        and write self.curves_array in 'curves' field
        """

        # first arg is GwyDatafield returned by get_gwyitem_object
        self.assertEqual(args[0], self.gwygraphmodel)

        # second arg is GwyfileError**
        assert ffi.typeof(args[1]) == ffi.typeof(ffi.new("GwyfileError**"))

        # last arg in Null
        self.assertEqual(args[-1], ffi.NULL)

        # combine fields names and fields pointers in one dictionary
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        arg_dict['curves'][0] = self.curves_array

        # C func returns true if the graphmodel object loock acceptable
        truep = ffi.new("bool*", True)
        return truep[0]


class GwyGraphModel_to_gwy(unittest.TestCase):
    """Tests for to_gwy method of GwyGraphModel class """
    def setUp(self):
        self.gwygraphmodel = Mock(spec=GwyGraphModel)
        self.ncurves = 2
        self.gwygraphmodel.curves = [GwyGraphCurve(np.random.rand(2, 10))
                                     for curve in range(self.ncurves)]
        self.gwygraphmodel.meta = {'title': 'Title',
                                   'top_label': '',
                                   'left_label': 'y',
                                   'right_label': '',
                                   'bottom_label': 'x',
                                   'x_unit': 'm',
                                   'y_unit': 'm',
                                   'x_min': 0.,
                                   'x_min_set': True,
                                   'x_max': 1.,
                                   'x_max_set': True,
                                   'x_is_logarithmic': False,
                                   'y_is_logarithmic': False,
                                   'label.visible': True,
                                   'label.has_frame': True,
                                   'label.reverse': False,
                                   'label.frame_thickness': 1,
                                   'label.position': 0,
                                   'grid-type': 1}
        self.gwygraphmodel.to_gwy = GwyGraphModel.to_gwy
        self.expected_return = Mock()

    @patch('pygwyfile.gwygraph.lib', autospec=True)
    def test_args_of_libgwyfile_func(self, mock_lib):
        """ Test args of gwyfile_object_new_graphmodel """
        mock_lib.gwyfile_object_new_graphmodel.side_effect = (
            self._side_effect)
        actual_return = self.gwygraphmodel.to_gwy(self.gwygraphmodel)
        self.assertEqual(actual_return, self.expected_return)

    def _side_effect(self, *args):

        self.assertEqual(int(args[0]), self.ncurves)

        self.assertEqual(ffi.string(args[1]), b"curves")

        self.assertEqual(ffi.string(args[3]), b"title")
        self.assertEqual(ffi.string(args[4]),
                         self.gwygraphmodel.meta['title'].encode('utf-8'))

        self.assertEqual(ffi.string(args[5]), b"top_label")
        self.assertEqual(
            ffi.string(args[6]),
            self.gwygraphmodel.meta['top_label'].encode('utf-8'))

        self.assertEqual(ffi.string(args[7]), b"left_label")
        self.assertEqual(
            ffi.string(args[8]),
            self.gwygraphmodel.meta['left_label'].encode('utf-8'))

        self.assertEqual(ffi.string(args[9]), b"right_label")
        self.assertEqual(
            ffi.string(args[10]),
            self.gwygraphmodel.meta['right_label'].encode('utf-8'))

        self.assertEqual(ffi.string(args[11]), b"bottom_label")
        self.assertEqual(
            ffi.string(args[12]),
            self.gwygraphmodel.meta['bottom_label'].encode('utf-8'))

        self.assertEqual(ffi.string(args[13]), b"x_unit")
        self.assertEqual(
            ffi.string(args[14]),
            self.gwygraphmodel.meta['x_unit'].encode('utf-8'))

        self.assertEqual(ffi.string(args[15]), b"y_unit")
        self.assertEqual(
            ffi.string(args[16]),
            self.gwygraphmodel.meta['y_unit'].encode('utf-8'))

        self.assertEqual(ffi.string(args[17]), b"x_min")
        self.assertEqual(float(args[18]), self.gwygraphmodel.meta['x_min'])

        self.assertEqual(ffi.string(args[19]), b"x_min_set")
        self.assertEqual(bool(args[20]), self.gwygraphmodel.meta['x_min_set'])

        self.assertEqual(ffi.string(args[21]), b"x_max")
        self.assertEqual(float(args[22]), self.gwygraphmodel.meta['x_max'])

        self.assertEqual(ffi.string(args[23]), b"x_max_set")
        self.assertEqual(bool(args[24]), self.gwygraphmodel.meta['x_max_set'])

        self.assertEqual(ffi.string(args[25]), b"x_is_logarithmic")
        self.assertEqual(bool(args[26]),
                         self.gwygraphmodel.meta['x_is_logarithmic'])

        self.assertEqual(ffi.string(args[27]), b"y_is_logarithmic")
        self.assertEqual(bool(args[28]),
                         self.gwygraphmodel.meta['y_is_logarithmic'])

        self.assertEqual(ffi.string(args[29]), b'label.visible')
        self.assertEqual(bool(args[30]),
                         self.gwygraphmodel.meta['label.visible'])

        self.assertEqual(ffi.string(args[31]), b"label.has_frame")
        self.assertEqual(bool(args[32]),
                         self.gwygraphmodel.meta['label.has_frame'])

        self.assertEqual(ffi.string(args[33]), b"label.reverse")
        self.assertEqual(bool(args[34]),
                         self.gwygraphmodel.meta['label.reverse'])

        self.assertEqual(ffi.string(args[35]), b'label.frame_thickness')
        self.assertEqual(int(args[36]),
                         self.gwygraphmodel.meta['label.frame_thickness'])

        self.assertEqual(ffi.string(args[37]), b'label.position')
        self.assertEqual(int(args[38]),
                         self.gwygraphmodel.meta['label.position'])

        self.assertEqual(ffi.string(args[39]), b'grid-type')
        self.assertEqual(int(args[40]),
                         self.gwygraphmodel.meta['grid-type'])

        self.assertEqual(args[-1], ffi.NULL)

        return self.expected_return


if __name__ == '__main__':
    unittest.main()
