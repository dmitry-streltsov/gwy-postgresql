import unittest
from unittest.mock import patch, call, Mock

import numpy as np

from gwydb.gwy._libgwyfile import ffi
from gwydb.gwy.gwyfile import GwyfileError, GwyfileErrorCMsg
from gwydb.gwy.gwyfile import Gwyfile
from gwydb.gwy.gwyselection import (GwyPointSelection,
                                    GwyPointerSelection,
                                    GwyLineSelection,
                                    GwyRectangleSelection,
                                    GwyEllipseSelection)
from gwydb.gwy.gwychannel import GwyDataField, GwyChannel


class GwyDataField_init(unittest.TestCase):
    """Test constructor of GwyDataField class
    """
    def setUp(self):
        self.test_data = np.random.rand(256, 256)
        self.test_meta = {'xres': 256,
                          'yres': 256,
                          'xreal': 1e-6,
                          'yreal': 1e-6,
                          'xoff': 0.,
                          'yoff': 0.,
                          'si_unit_xy': 'm',
                          'si_unit_z': 'A'}

    def test_init_with_test_data(self):
        """Test __init__ with data and meta args
        """
        gwydf = GwyDataField(data=self.test_data, meta=self.test_meta)
        np.testing.assert_almost_equal(gwydf.data, self.test_data)
        self.assertDictEqual(self.test_meta, gwydf.meta)

    def test_init_with_empty_meta(self):
        """Test __init__ with empty meta arg
        """
        gwydf = GwyDataField(data=self.test_data)
        np.testing.assert_almost_equal(gwydf.data, self.test_data)
        self.assertDictEqual(gwydf.meta,
                             {'xres': 256,
                              'yres': 256,
                              'xreal': 1.,
                              'yreal': 1.,
                              'xoff': 0.,
                              'yoff': 0.,
                              'si_unit_xy': '',
                              'si_unit_z': ''})

    def test_raise_ValueError_if_mismatched_data_shape_and_xres_yres(self):
        """Raise ValueError if data.shape is not equal meta['xres'], meta['yres']
        """
        test_meta = {'xres': 128,
                     'yres': 128}  # self.test_data.shape = 256, 256
        self.assertRaises(ValueError,
                          GwyDataField,
                          data=self.test_data,
                          meta=test_meta)


class GwyDataField_from_gwy(unittest.TestCase):
    """Test from_gwy method of GwyDataField class
    """
    @patch('gwydb.gwy.gwychannel.GwyDataField', autospec=True)
    @patch.object(GwyDataField, '_get_data')
    @patch.object(GwyDataField, '_get_meta')
    def test_GwyDataField_from_gwy(self,
                                   mock_get_meta,
                                   mock_get_data,
                                   mock_GwyDataField):
        """ Get metadata and data from <GwyDatafield*> object, init GwyDatafield
            and return the latter
        """
        cgwydf = Mock()
        test_meta = {'xres': 256,
                     'yres': 256,
                     'xreal': 1e-6,
                     'yreal': 1e-6,
                     'xoff': 0.,
                     'yoff': 0.,
                     'si_unit_xy': 'm',
                     'si_unit_z': 'A'}
        test_data = np.random.rand(256, 256)
        mock_get_meta.return_value = test_meta
        mock_get_data.return_value = test_data
        gwydf = GwyDataField.from_gwy(cgwydf)
        mock_get_meta.assert_has_calls(
            [call(cgwydf)])
        mock_get_data.assert_has_calls(
            [call(cgwydf, test_meta['xres'], test_meta['yres'])])
        mock_GwyDataField.assert_has_calls(
            [call(data=test_data, meta=test_meta)])
        self.assertEqual(gwydf, mock_GwyDataField(data=test_data,
                                                  meta=test_meta))


class GwyDataField_get_meta(unittest.TestCase):
    """Test _get_meta method of GwyDataFieldself
    """

    def setUp(self):
        self.cgwydf = Mock()
        self.mock_gwydf = Mock(spec=GwyDataField)
        self.mock_gwydf._get_meta = GwyDataField._get_meta

        patcher_lib = patch('gwydb.gwy.gwychannel.lib',
                            autospec=True)
        self.addCleanup(patcher_lib.stop)
        self.mock_lib = patcher_lib.start()

        self.falsep = ffi.new("bool*", False)
        self.truep = ffi.new("bool*", True)
        self.errorp = ffi.new("GwyfileError**")
        self.error_msg = "Test error message"
        self.metadata_dict = {'xres': ffi.typeof(ffi.new("int32_t*")),
                              'yres': ffi.typeof(ffi.new("int32_t*")),
                              'xreal': ffi.typeof(ffi.new("double*")),
                              'yreal': ffi.typeof(ffi.new("double*")),
                              'xoff': ffi.typeof(ffi.new("double*")),
                              'yoff': ffi.typeof(ffi.new("double*")),
                              'si_unit_xy': ffi.typeof(ffi.new("char**")),
                              'si_unit_z': ffi.typeof(ffi.new("char**"))}

    def test_raise_exception_if_df_loock_unacceptable(self):
        """Raise GywfileErrorCMsg if gwyfile_object_datafield_get returns False
        """

        self.mock_lib.gwyfile_object_datafield_get.return_value = (
            self.falsep[0])
        self.assertRaises(GwyfileErrorCMsg,
                          self.mock_gwydf._get_meta,
                          self.cgwydf)

    def test_libgwyfile_function_args(self):
        """
        Test args of gwyfile_object_datafield_get C function
        """

        self.mock_lib.gwyfile_object_datafield_get.side_effect = (
            self._side_effect_check_args)
        self.mock_gwydf._get_meta(self.cgwydf)

    def _side_effect_check_args(self, *args):
        """
        Check args passing to gwyfile_object_datafield_get C function
        """

        # first arg is GwyDatafield object from Libgwyfile
        self.assertEqual(args[0], self.cgwydf)

        # second arg is GwyfileError**
        assert ffi.typeof(args[1]) == ffi.typeof(self.errorp)

        # last arg in NULL
        self.assertEqual(args[-1], ffi.NULL)

        # create dict from names and types of pointers in args
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointer_types = [ffi.typeof(pointer) for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointer_types))

        self.assertDictEqual(arg_dict, self.metadata_dict)

        return self.truep[0]

    def test_returned_metadata_dict(self):
        """
        Returns dictionary with metadata
        """

        self.test_metadata_dict = {'xres': 256,
                                   'yres': 256,
                                   'xreal': 1e-6,
                                   'yreal': 1e-6,
                                   'xoff': 0,
                                   'yoff': 0,
                                   'si_unit_xy': 'm',
                                   'si_unit_z': 'A'}
        self.mock_lib.gwyfile_object_datafield_get.side_effect = (
            self._side_effect_return_metadata)

        meta = self.mock_gwydf._get_meta(self.cgwydf)
        self.assertDictEqual(self.test_metadata_dict, meta)

    def _side_effect_return_metadata(self, *args):

        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        for key in arg_dict:
            if key not in ['si_unit_xy', 'si_unit_z']:
                arg_dict[key][0] = self.test_metadata_dict[key]
            else:
                metadata_value = self.test_metadata_dict[key].encode('utf-8')
                metadata_c_str = ffi.new("char[]", metadata_value)
                arg_dict[key][0] = metadata_c_str
        return self.truep[0]


class GwyDataField_get_data(unittest.TestCase):
    """Test _get_data method of GwyDataField class
    """

    def setUp(self):
        self.cgwydf = Mock()
        self.mock_gwydf = Mock(spec=GwyDataField)
        self.mock_gwydf._get_data = GwyDataField._get_data

        patcher_lib = patch('gwydb.gwy.gwychannel.lib',
                            autospec=True)
        self.addCleanup(patcher_lib.stop)
        self.mock_lib = patcher_lib.start()

        self.falsep = ffi.new("bool*", False)
        self.truep = ffi.new("bool*", True)
        self.errorp = ffi.new("GwyfileError**")
        self.error_msg = "Test error message"

        self.xres = 256
        self.yres = 256
        self.data = np.random.rand(self.xres, self.yres)

    def test_raise_exception__df_looks_unacceptable(self):
        """Raise GwyfileErrorCMsg if datafield object loosk unacceptable

        Raise GwyfileErrorCMsg exception if
        gwyfile_object_datafield_get returns False
        """

        self.mock_lib.gwyfile_object_datafield_get.return_value = (
            self.falsep[0])
        self.assertRaises(GwyfileErrorCMsg,
                          self.mock_gwydf._get_data,
                          self.cgwydf,
                          self.xres,
                          self.yres)

    def test_returned_data(self):
        """
        Check returned value
        """

        self.mock_lib.gwyfile_object_datafield_get.side_effect = (
            self._side_effect)

        data = self.mock_gwydf._get_data(self.cgwydf,
                                         self.xres,
                                         self.yres)

        np.testing.assert_almost_equal(self.data, data)

    def _side_effect(self, *args):

        # first arg is GwyDatafield object from Libgwyfile
        self.assertEqual(args[0], self.cgwydf)

        # second arg is GwyfileError**
        assert ffi.typeof(args[1]) == ffi.typeof(self.errorp)

        # last arg in NULL
        self.assertEqual(args[-1], ffi.NULL)

        # create dict from names and types of pointers in args
        arg_keys = [ffi.string(key).decode('utf-8') for key in args[2:-1:2]]
        arg_pointers = [pointer for pointer in args[3:-1:2]]
        arg_dict = dict(zip(arg_keys, arg_pointers))

        datap = arg_dict['data']
        datap[0] = ffi.cast("double*", self.data.ctypes.data)

        return self.truep[0]


class GwyChannel_get_title(unittest.TestCase):
    """Test _get_title method of GwyChannel class
    """

    def setUp(self):
        self.gwyfile = Mock(spec=Gwyfile)
        self.channel_id = 0
        self.gwyfile.get_gwyobject.return_value = (
            ffi.new("char[]", b"Title"))

    def test_raise_exception_if_gwyobject_does_not_exist(self):
        """Raise GwyFileError is title gwyobject does not exist
        """
        self.gwyfile.check_gwyobject.return_value = False
        self.assertRaises(GwyfileError,
                          GwyChannel._get_title,
                          self.gwyfile,
                          self.channel_id)

    def test_check_args_passing_to_get_gwyobject(self):
        """
        Check args passing to Gwyfile.get_gwyobject method
        """

        GwyChannel._get_title(self.gwyfile, self.channel_id)
        self.gwyfile.get_gwyobject.assert_has_calls(
            [call("/{:d}/data/title".format(self.channel_id))])

    def test_returned_value(self):
        """
        Check returned value of get_title method
        """

        title = GwyChannel._get_title(self.gwyfile, self.channel_id)
        self.assertEqual(title, 'Title')


class GwyChannel_get_visibility(unittest.TestCase):
    """Test _get_visibility method of GwyChannel class
    """

    def setUp(self):
        self.gwyfile = Mock(spec=Gwyfile)
        self.channel_id = 0

    def test_check_if_visibility_flag_exists(self):
        """ Check existence of visibility flag
        """
        key = "/{:d}/data/visible".format(self.channel_id)
        self.gwyfile.check_gwyobject.return_value = False
        GwyChannel._get_visibility(self.gwyfile, self.channel_id)
        self.gwyfile.check_gwyobject.assert_has_calls(
            [call(key)])

    def test_return_False_if_gwyobject_does_not_exist(self):
        """ Return False if gwyfile.check_gwyobject returned False
        """
        self.gwyfile.check_gwyobject.return_value = False
        visible = GwyChannel._get_visibility(self.gwyfile, self.channel_id)
        self.assertIs(visible, False)

    def test_get_gwyobject_if_it_exists(self):
        """ If gwyobject exists get it
        """
        key = "/{:d}/data/visible".format(self.channel_id)
        self.gwyfile.check_gwyobject.return_value = True
        truep = ffi.new("bool*", True)
        self.gwyfile.get_gwyobject.return_value = truep[0]
        GwyChannel._get_visibility(self.gwyfile, self.channel_id)
        self.gwyfile.get_gwyobject.assert_has_calls(
            [call(key)])

    def test_return_True_if_visibility_flag_is_True(self):
        """Return True if visibility flag exists and it is True
        """
        self.gwyfile.check_gwyobject.return_value = True
        truep = ffi.new("bool*", True)
        self.gwyfile.get_gwyobject.return_value = truep[0]
        visible = GwyChannel._get_visibility(self.gwyfile, self.channel_id)
        self.assertIs(visible, True)

    def test_return_False_if_visibility_flag_is_False(self):
        """Return False if visibility flag exists and it is False
        """
        self.gwyfile.check_gwyobject.return_value = True
        falsep = ffi.new("bool*", False)
        self.gwyfile.get_gwyobject.return_value = falsep[0]
        visible = GwyChannel._get_visibility(self.gwyfile, self.channel_id)
        self.assertIs(visible, False)


class GwyChannel_get_data(unittest.TestCase):
    """Test _get_data method of GwyChannel class
    """

    def setUp(self):
        self.gwyfile = Mock(spec=Gwyfile)
        self.channel_id = 0
        patcher = patch('gwydb.gwy.gwychannel.GwyDataField',
                        autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_GwyDataField = patcher.start()

    def test_raise_exception_if_gwydatafield_does_not_exist(self):
        """Raise GwyFileError is <GwyDataField*>  object does not exist
        """
        self.gwyfile.check_gwyobject.return_value = False
        self.assertRaises(GwyfileError,
                          GwyChannel._get_data,
                          self.gwyfile,
                          self.channel_id)

    def test_check_args_passing_to_get_gwyobject(self):
        """
        Check args passing to Gwyfile.get_gwyobject method
        """

        GwyChannel._get_data(self.gwyfile, self.channel_id)
        self.gwyfile.get_gwyobject.assert_has_calls(
            [call("/{:d}/data".format(self.channel_id))])

    def test_call_GwyDataField_constructor(self):
        """
        Pass gwydatafield object to GwyDataField constructor
        """

        gwydatafield = self.gwyfile.get_gwyobject.return_value
        GwyChannel._get_data(self.gwyfile, self.channel_id)
        self.mock_GwyDataField.from_gwy.assert_has_calls(
            [call(gwydatafield)])

    def test_check_returned_value(self):
        """
        Return object returned by GwyDataField constructor
        """

        expected_return = self.mock_GwyDataField.from_gwy.return_value
        actual_return = GwyChannel._get_data(self.gwyfile, self.channel_id)
        self.assertIs(expected_return, actual_return)


class GwyChannel_get_mask(unittest.TestCase):
    """Test _get_mask method of GwyChannel class
    """

    def setUp(self):
        self.gwyfile = Mock(spec=Gwyfile)
        self.channel_id = 0
        patcher = patch('gwydb.gwy.gwychannel.GwyDataField',
                        autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_GwyDataField = patcher.start()

    def test_check_existence_of_mask_datafield(self):
        """Check that mask <GwyDataField*> exists
        """
        GwyChannel._get_mask(self.gwyfile, self.channel_id)
        self.gwyfile.check_gwyobject.assert_has_calls(
            [call("/{:d}/mask".format(self.channel_id))])

    def test_return_None_if_mask_datafield_does_not_exist(self):
        """Return None if mask <GwyDataField*> does not exist
        """
        self.gwyfile.check_gwyobject.return_value = False
        actual_return = GwyChannel._get_mask(self.gwyfile,
                                             self.channel_id)
        self.assertIsNone(actual_return)

    def test_check_args_passing_to_get_gwyobject(self):
        """
        Check args passing to Gwyfile.get_gwyobject method
        """

        GwyChannel._get_mask(self.gwyfile, self.channel_id)
        self.gwyfile.get_gwyobject.assert_has_calls(
            [call("/{:d}/mask".format(self.channel_id))])

    def test_call_GwyDataField_constructor(self):
        """
        Pass gwydatafield object to GwyDataField constructor
        """

        gwydatafield = self.gwyfile.get_gwyobject.return_value
        GwyChannel._get_mask(self.gwyfile, self.channel_id)
        self.mock_GwyDataField.from_gwy.assert_has_calls(
            [call(gwydatafield)])

    def test_check_returned_value(self):
        """
        Return object returned by GwyDataField constructor
        """

        expected_return = self.mock_GwyDataField.from_gwy.return_value
        actual_return = GwyChannel._get_mask(self.gwyfile, self.channel_id)
        self.assertIs(expected_return, actual_return)


class GwyChannel_get_show(unittest.TestCase):
    """Test _get_show method of GwyChannel class
    """

    def setUp(self):
        self.gwyfile = Mock(spec=Gwyfile)
        self.channel_id = 0
        patcher = patch('gwydb.gwy.gwychannel.GwyDataField',
                        autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_GwyDataField = patcher.start()

    def test_check_existence_of_show_datafield(self):
        """Check that presentation <GwyDataField*> exists
        """
        GwyChannel._get_show(self.gwyfile, self.channel_id)
        self.gwyfile.check_gwyobject.assert_has_calls(
            [call("/{:d}/show".format(self.channel_id))])

    def test_return_None_if_show_datafield_does_not_exist(self):
        """Return None if presentation <GwyDataField*> does not exist
        """
        self.gwyfile.check_gwyobject.return_value = False
        actual_return = GwyChannel._get_show(self.gwyfile,
                                             self.channel_id)
        self.assertIsNone(actual_return)

    def test_check_args_passing_to_get_gwyobject(self):
        """
        Check args passing to Gwyfile.get_gwyobject method
        """

        GwyChannel._get_show(self.gwyfile, self.channel_id)
        self.gwyfile.get_gwyobject.assert_has_calls(
            [call("/{:d}/show".format(self.channel_id))])

    def test_call_GwyDataField_constructor(self):
        """
        Pass gwydatafield object to GwyDataField constructor
        """

        gwydatafield = self.gwyfile.get_gwyobject.return_value
        GwyChannel._get_show(self.gwyfile, self.channel_id)
        self.mock_GwyDataField.from_gwy.assert_has_calls(
            [call(gwydatafield)])

    def test_check_returned_value(self):
        """
        Return object returned by GwyDataField constructor
        """

        expected_return = self.mock_GwyDataField.from_gwy.return_value
        actual_return = GwyChannel._get_show(self.gwyfile, self.channel_id)
        self.assertIs(expected_return, actual_return)


class GwyChannel_get_point_sel(unittest.TestCase):
    """Test _get_point_sel method of GwyChannel class
    """

    def setUp(self):
        self.gwyfile = Mock(spec=Gwyfile)
        self.channel_id = 0
        patcher = patch('gwydb.gwy.gwychannel.GwyPointSelection',
                        autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_GwyPointSelection = patcher.start()

    def test_check_existence_of_point_selections(self):
        """Check that point selections exists in the channel
        """
        GwyChannel._get_point_sel(self.gwyfile, self.channel_id)
        self.gwyfile.check_gwyobject.assert_has_calls(
            [call("/{:d}/select/point".format(self.channel_id))])

    def test_return_None_if_point_selections_do_not_exist(self):
        """Return None if point selections do not exist
        """
        self.gwyfile.check_gwyobject.return_value = False
        actual_return = GwyChannel._get_point_sel(self.gwyfile,
                                                  self.channel_id)
        self.assertIsNone(actual_return)

    def test_check_args_passing_to_get_gwyobject(self):
        """
        Check args passing to Gwyfile.get_gwyobject method
        """

        GwyChannel._get_point_sel(self.gwyfile, self.channel_id)
        self.gwyfile.get_gwyobject.assert_has_calls(
            [call("/{:d}/select/point".format(self.channel_id))])

    def test_call_GwyPointSelections_constructor(self):
        """
        Pass gwypointselection object to GwyPointSelection.from_gwy method
        """

        gwypointsel = self.gwyfile.get_gwyobject.return_value
        GwyChannel._get_point_sel(self.gwyfile, self.channel_id)
        self.mock_GwyPointSelection.from_gwy.assert_has_calls(
            [call(gwypointsel)])

    def test_check_returned_value(self):
        """
        Return object returned by GwyPointSelection constructor
        """

        expected_return = self.mock_GwyPointSelection.from_gwy.return_value
        actual_return = GwyChannel._get_point_sel(self.gwyfile,
                                                  self.channel_id)
        self.assertIs(expected_return, actual_return)


class GwyChannel_get_pointer_sel(unittest.TestCase):
    """Test _get_pointer_sel method of GwyChannel class
    """

    def setUp(self):
        self.gwyfile = Mock(spec=Gwyfile)
        self.channel_id = 0
        patcher = patch('gwydb.gwy.gwychannel.GwyPointerSelection',
                        autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_GwyPointerSelection = patcher.start()

    def test_check_existence_of_pointer_selections(self):
        """Check that pointer selections exists in the channel
        """
        GwyChannel._get_pointer_sel(self.gwyfile, self.channel_id)
        self.gwyfile.check_gwyobject.assert_has_calls(
            [call("/{:d}/select/pointer".format(self.channel_id))])

    def test_return_None_if_pointer_selections_do_not_exist(self):
        """Return None if pointer selections do not exist
        """
        self.gwyfile.check_gwyobject.return_value = False
        actual_return = GwyChannel._get_pointer_sel(self.gwyfile,
                                                    self.channel_id)
        self.assertIsNone(actual_return)

    def test_check_args_passing_to_get_gwyobject(self):
        """
        Check args passing to Gwyfile.get_gwyobject method
        """

        GwyChannel._get_pointer_sel(self.gwyfile, self.channel_id)
        self.gwyfile.get_gwyobject.assert_has_calls(
            [call("/{:d}/select/pointer".format(self.channel_id))])

    def test_call_GwyPointSelection_constructor(self):
        """
        Pass gwypointselection object to GwyPointerSelection constructor
        """

        gwypointersel = self.gwyfile.get_gwyobject.return_value
        GwyChannel._get_pointer_sel(self.gwyfile, self.channel_id)
        self.mock_GwyPointerSelection.from_gwy.assert_has_calls(
            [call(gwypointersel)])

    def test_check_returned_value(self):
        """
        Return object returned by GwyPointerSelection constructor
        """

        expected_return = self.mock_GwyPointerSelection.from_gwy.return_value
        actual_return = GwyChannel._get_pointer_sel(self.gwyfile,
                                                    self.channel_id)
        self.assertIs(expected_return, actual_return)


class GwyChannel_get_line_sel(unittest.TestCase):
    """Test _get_line_sel method of GwyChannel class
    """

    def setUp(self):
        self.gwyfile = Mock(spec=Gwyfile)
        self.channel_id = 0
        patcher = patch('gwydb.gwy.gwychannel.GwyLineSelection',
                        autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_GwyLineSelection = patcher.start()

    def test_check_existence_of_line_selections(self):
        """Check that line selections exists in the channel
        """
        GwyChannel._get_line_sel(self.gwyfile, self.channel_id)
        self.gwyfile.check_gwyobject.assert_has_calls(
            [call("/{:d}/select/line".format(self.channel_id))])

    def test_return_None_if_line_selections_do_not_exist(self):
        """Return None if line selections do not exist
        """
        self.gwyfile.check_gwyobject.return_value = False
        actual_return = GwyChannel._get_line_sel(self.gwyfile,
                                                 self.channel_id)
        self.assertIsNone(actual_return)

    def test_check_args_passing_to_get_gwyobject(self):
        """
        Check args passing to Gwyfile.get_gwyobject method
        """

        GwyChannel._get_line_sel(self.gwyfile, self.channel_id)
        self.gwyfile.get_gwyobject.assert_has_calls(
            [call("/{:d}/select/line".format(self.channel_id))])

    def test_call_GwyLineSelection_constructor(self):
        """
        Pass gwylineselection object to GwyLineSelection constructor
        """

        gwylinesel = self.gwyfile.get_gwyobject.return_value
        GwyChannel._get_line_sel(self.gwyfile, self.channel_id)
        self.mock_GwyLineSelection.from_gwy.assert_has_calls(
            [call(gwylinesel)])

    def test_check_returned_value(self):
        """
        Return object returned by GwyLineSelection constructor
        """

        expected_return = self.mock_GwyLineSelection.from_gwy.return_value
        actual_return = GwyChannel._get_line_sel(self.gwyfile,
                                                 self.channel_id)
        self.assertIs(expected_return, actual_return)


class GwyChannel_get_rectangle_sel(unittest.TestCase):
    """Test _get_rectangle_sel method of GwyChannel class
    """

    def setUp(self):
        self.gwyfile = Mock(spec=Gwyfile)
        self.channel_id = 0
        patcher = patch('gwydb.gwy.gwychannel.GwyRectangleSelection',
                        autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_GwyRectangleSelection = patcher.start()

    def test_check_existence_of_rectangle_selections(self):
        """Check that rectangle selections exists in the channel
        """
        GwyChannel._get_rectangle_sel(self.gwyfile, self.channel_id)
        self.gwyfile.check_gwyobject.assert_has_calls(
            [call("/{:d}/select/rectangle".format(self.channel_id))])

    def test_return_None_if_rectangle_selections_do_not_exist(self):
        """Return None if rectangle selections do not exist
        """
        self.gwyfile.check_gwyobject.return_value = False
        actual_return = GwyChannel._get_rectangle_sel(self.gwyfile,
                                                      self.channel_id)
        self.assertIsNone(actual_return)

    def test_check_args_passing_to_get_gwyobject(self):
        """
        Check args passing to Gwyfile.get_gwyobject method
        """

        GwyChannel._get_rectangle_sel(self.gwyfile, self.channel_id)
        self.gwyfile.get_gwyobject.assert_has_calls(
            [call("/{:d}/select/rectangle".format(self.channel_id))])

    def test_call_GwyRectangleSelections_constructor(self):
        """
        Pass gwyrectangleselection object to GwyRectangleSelection constructor
        """

        gwyrectsel = self.gwyfile.get_gwyobject.return_value
        GwyChannel._get_rectangle_sel(self.gwyfile, self.channel_id)
        self.mock_GwyRectangleSelection.from_gwy.assert_has_calls(
            [call(gwyrectsel)])

    def test_check_returned_value(self):
        """
        Return object returned by GwyRectangleSelection constructor
        """

        expected_return = (
            self.mock_GwyRectangleSelection.from_gwy.return_value)
        actual_return = GwyChannel._get_rectangle_sel(self.gwyfile,
                                                      self.channel_id)
        self.assertIs(expected_return, actual_return)


class GwyChannel_get_ellipse_sel(unittest.TestCase):
    """Test _get_ellipse_sel method of GwyChannel class
    """

    def setUp(self):
        self.gwyfile = Mock(spec=Gwyfile)
        self.channel_id = 0
        patcher = patch('gwydb.gwy.gwychannel.GwyEllipseSelection',
                        autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_GwyEllipseSelection = patcher.start()

    def test_check_existence_of_ellipse_selections(self):
        """Check that ellipse selections exists in the channel
        """
        GwyChannel._get_ellipse_sel(self.gwyfile, self.channel_id)
        self.gwyfile.check_gwyobject.assert_has_calls(
            [call("/{:d}/select/ellipse".format(self.channel_id))])

    def test_return_None_if_ellipse_selections_do_not_exist(self):
        """Return None if ellipse selections do not exist
        """
        self.gwyfile.check_gwyobject.return_value = False
        actual_return = GwyChannel._get_ellipse_sel(self.gwyfile,
                                                    self.channel_id)
        self.assertIsNone(actual_return)

    def test_check_args_passing_to_get_gwyobject(self):
        """Check args passing to Gwyfile.get_gwyobject method
        """

        GwyChannel._get_ellipse_sel(self.gwyfile, self.channel_id)
        self.gwyfile.get_gwyobject.assert_has_calls(
            [call("/{:d}/select/ellipse".format(self.channel_id))])

    def test_call_GwyEllipseSelection_constructor(self):
        """Pass gwyellipseselection object to GwyEllipseSelection constructor
        """

        gwyellipsesel = self.gwyfile.get_gwyobject.return_value
        GwyChannel._get_ellipse_sel(self.gwyfile, self.channel_id)
        self.mock_GwyEllipseSelection.from_gwy.assert_has_calls(
             [call(gwyellipsesel)])

    def test_check_returned_value(self):
        """Return object returned by GwyEllipseSelections constructor
        """

        expected_return = self.mock_GwyEllipseSelection.from_gwy.return_value
        actual_return = GwyChannel._get_ellipse_sel(self.gwyfile,
                                                    self.channel_id)
        self.assertIs(expected_return, actual_return)


class GwyChannel_init(unittest.TestCase):
    """Test init method of GwyChannel class
    """

    def test_raise_TypeError_if_data_is_not_GwyDataField(self):
        """Raise TypeError exception if data is not GwyDataField instance
        """
        data = np.zeros(10)
        self.assertRaises(TypeError,
                          GwyChannel,
                          title='Title',
                          data=data)

    def test_raise_TypeError_if_mask_is_not_GwyDataField_or_None(self):
        """Raise TypeError exception if mask is not GwyDataField instance or None
        """
        data = Mock(spec=GwyDataField)
        mask = np.zeros(10)
        self.assertRaises(TypeError,
                          GwyChannel,
                          title='Title',
                          data=data,
                          mask=mask)

    def test_raise_TypeError_if_show_is_not_GwyDataField_or_None(self):
        """Raise TypeError exception if show is not GwyDataField instance or None
        """
        data = Mock(spec=GwyDataField)
        show = np.zeros(10)
        self.assertRaises(TypeError,
                          GwyChannel,
                          title='Title',
                          data=data,
                          show=show)

    def test_raise_TypeError_if_point_sel_is_not_GwyPointSelection(self):
        """Raise TypeError exception if point_sel is not GwyPointSelection
        instance or None
        """
        data = Mock(spec=GwyDataField)
        point_sel = (0., 0.)
        self.assertRaises(TypeError,
                          GwyChannel,
                          title='Title',
                          data=data,
                          point_sel=point_sel)

    def test_raise_TypeError_if_pointer_sel_is_not_GwyPointerSelection(self):
        """Raise TypeError exception if pointer_sel is not GwyPointerSelection
        instance or None
        """
        data = Mock(spec=GwyDataField)
        pointer_sel = (0., 0.)
        self.assertRaises(TypeError,
                          GwyChannel,
                          title='Title',
                          data=data,
                          pointer_sel=pointer_sel)

    def test_raise_TypeError_if_line_sel_is_not_GwyLineSelection(self):
        """Raise TypeError exception if line_sel is not GwyLineSelection
        instance or None
        """
        data = Mock(spec=GwyDataField)
        line_sel = ((0., 0.), (1., 1.))
        self.assertRaises(TypeError,
                          GwyChannel,
                          title='Title',
                          data=data,
                          line_sel=line_sel)

    def test_raise_TypeError_if_rectangle_sel_is_of_wrong_type(self):
        """Raise TypeError exception if rectangle_sel is not GwyRectangleSelection
        instance or None
        """
        data = Mock(spec=GwyDataField)
        rectangle_sel = ((0., 0.), (1., 1.))
        self.assertRaises(TypeError,
                          GwyChannel,
                          title='Title',
                          data=data,
                          rectangle_sel=rectangle_sel)

    def test_raise_TypeError_if_ellipse_sel_is_not_GwyEllipseSelection(self):
        """Raise TypeError exception if ellipse_sel is not GwyEllipseSelection
        instance or None
        """
        data = Mock(spec=GwyDataField)
        ellipse_sel = ((0., 0.), (1., 1.))
        self.assertRaises(TypeError,
                          GwyChannel,
                          title='Title',
                          data=data,
                          ellipse_sel=ellipse_sel)

    def test_title_data_attributes(self):
        """Check title and data attributes of GwyChannel
        """
        data = Mock(spec=GwyDataField)
        title = 'Title'
        channel = GwyChannel(title=title, data=data)
        self.assertEqual(channel.title, title)
        self.assertEqual(channel.data, data)

    def test_mask_show_attribute(self):
        """Check mask and show attributes of GwyChannel
        """
        data = Mock(spec=GwyDataField)
        title = 'Title'
        mask = Mock(spec=GwyDataField)
        show = Mock(spec=GwyDataField)
        channel = GwyChannel(title=title, data=data,
                             mask=mask, show=show)
        self.assertEqual(channel.mask, mask)
        self.assertEqual(channel.show, show)

    def test_selections_attributes(self):
        """Check *_selections attributes
        """
        data = Mock(spec=GwyDataField)
        title = 'Title'
        point_sel = Mock(spec=GwyPointSelection)
        pointer_sel = Mock(spec=GwyPointerSelection)
        line_sel = Mock(spec=GwyLineSelection)
        rectangle_sel = Mock(spec=GwyRectangleSelection)
        ellipse_sel = Mock(spec=GwyEllipseSelection)

        channel = GwyChannel(title=title, data=data,
                             point_sel=point_sel,
                             pointer_sel=pointer_sel,
                             line_sel=line_sel,
                             rectangle_sel=rectangle_sel,
                             ellipse_sel=ellipse_sel)
        self.assertEqual(channel.point_selections,
                         point_sel)
        self.assertEqual(channel.pointer_selections,
                         pointer_sel)
        self.assertEqual(channel.line_selections,
                         line_sel)
        self.assertEqual(channel.rectangle_selections,
                         rectangle_sel)
        self.assertEqual(channel.ellipse_selections,
                         ellipse_sel)


class GwyChannel_from_gwy(unittest.TestCase):
    """Test from_gwy method of GwyChannel class """

    def test_raise_TypeError_if_gwyfile_is_of_wrong_type(self):
        """Raise TypeError exception if gwyfile is not Gwyfile instance """
        self.assertRaises(TypeError, GwyChannel.from_gwy, 'test_string',
                          0)

    @patch('gwydb.gwy.gwychannel.GwyChannel', autospec=True)
    @patch.object(GwyChannel, '_get_title')
    @patch.object(GwyChannel, '_get_data')
    @patch.object(GwyChannel, '_get_mask')
    @patch.object(GwyChannel, '_get_show')
    @patch.object(GwyChannel, '_get_point_sel')
    @patch.object(GwyChannel, '_get_pointer_sel')
    @patch.object(GwyChannel, '_get_line_sel')
    @patch.object(GwyChannel, '_get_rectangle_sel')
    @patch.object(GwyChannel, '_get_ellipse_sel')
    @patch.object(GwyChannel, '_get_visibility')
    def test_args_of_other_calls(self,
                                 mock_get_visibility,
                                 mock_get_ellipse_sel,
                                 mock_get_rectangle_sel,
                                 mock_get_line_sel,
                                 mock_get_pointer_sel,
                                 mock_get_point_sel,
                                 mock_get_show,
                                 mock_get_mask,
                                 mock_get_data,
                                 mock_get_title,
                                 mock_GwyChannel):
        gwyfile = Mock(spec=Gwyfile)
        channel_id = 0

        title = 'Title'
        mock_get_title.return_value = title

        data = Mock(spec=GwyDataField)
        mock_get_data.return_value = data

        visible = True
        visiblep = ffi.new("bool*", visible)
        mock_get_visibility.return_value = visiblep[0]

        mask = Mock(spec=GwyDataField)
        mock_get_mask.return_value = mask

        show = Mock(spec=GwyDataField)
        mock_get_show.return_value = show

        point_sel = Mock(spec=GwyPointSelection)
        mock_get_point_sel.return_value = point_sel

        pointer_sel = Mock(spec=GwyPointerSelection)
        mock_get_pointer_sel.return_value = pointer_sel

        line_sel = Mock(spec=GwyLineSelection)
        mock_get_line_sel.return_value = line_sel

        rectangle_sel = Mock(spec=GwyRectangleSelection)
        mock_get_rectangle_sel.return_value = rectangle_sel

        ellipse_sel = Mock(spec=GwyEllipseSelection)
        mock_get_ellipse_sel.return_value = ellipse_sel

        channel = GwyChannel.from_gwy(gwyfile, channel_id)

        mock_get_title.assert_has_calls(
            [call(gwyfile, channel_id)])

        mock_get_data.assert_has_calls(
            [call(gwyfile, channel_id)])

        mock_get_mask.assert_has_calls(
            [call(gwyfile, channel_id)])

        mock_get_visibility.assert_has_calls(
            [call(gwyfile, channel_id)])

        mock_get_point_sel.assert_has_calls(
            [call(gwyfile, channel_id)])

        mock_get_pointer_sel.assert_has_calls(
            [call(gwyfile, channel_id)])

        mock_get_line_sel.assert_has_calls(
            [call(gwyfile, channel_id)])

        mock_get_rectangle_sel.assert_has_calls(
            [call(gwyfile, channel_id)])

        mock_get_ellipse_sel.assert_has_calls(
            [call(gwyfile, channel_id)])

        self.assertEqual(channel, mock_GwyChannel.return_value)

        mock_GwyChannel.assert_has_calls(
            [call(title=title,
                  data=data,
                  visible=visible,
                  mask=mask,
                  show=show,
                  point_sel=point_sel,
                  pointer_sel=pointer_sel,
                  line_sel=line_sel,
                  rectangle_sel=rectangle_sel,
                  ellipse_sel=ellipse_sel)])
