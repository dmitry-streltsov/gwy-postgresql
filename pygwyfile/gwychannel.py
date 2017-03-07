""" Pythonic representation of gwyddion channel objects

    Classes:
        GwyChannel:   pythonic representation of gwyddion channel

"""
from pygwyfile.gwyfile import GwyfileError
from pygwyfile.gwyfile import Gwyfile
from pygwyfile.gwydatafield import GwyDataField
from pygwyfile.gwyselection import (GwyPointSelection,
                                    GwyPointerSelection,
                                    GwyLineSelection,
                                    GwyRectangleSelection,
                                    GwyEllipseSelection)


class GwyChannel:
    """Class for GwyChannel representation

    Attributes:
        title (string): channel title, as shown in the data browser
        data (GwyDataField): channel data
        visible (boolean): whether the channel should be displayed in
                           a window when the file is loaded
        palette (string): name of the false color gradient used to
                          display the channel
        range_type (int): flase color mapping type
        mask (GwyDataField): mask data
        show (GwyDataField): presentation data
        point_selections (GwyPointSelection): point selections
        pointer_selections (GwyPointerSelection): pointer selections
        line_selections (GwyLineSelection): line selections
        rectangle_selections (GwyRectangleSelection): rectange selections
        ellipse_selections (GwyEllipseSelection): ellipse selections

    Methods:
        from_gwy(gwyfile, channel_id): Get channel with id=channel_id
                                       from Gwyfile object

    """

    def __init__(self, title, data, visible=False,
                 palette=None, range_type=None,
                 range_min=None, range_max=None,
                 mask=None,
                 mask_red=None, mask_green=None,
                 mask_blue=None, mask_alpha=None,
                 show=None,
                 point_sel=None, pointer_sel=None,
                 line_sel=None, rectangle_sel=None,
                 ellipse_sel=None):

        self.title = title
        self.visible = visible
        self.palette = palette
        self.range_type = range_type
        self.range_min = range_min
        self.range_max = range_max
        self.mask_red = mask_red
        self.mask_green = mask_green
        self.mask_blue = mask_blue
        self.mask_alpha = mask_alpha

        if not isinstance(data, GwyDataField):
            raise TypeError("data must be an instance of GwyDataField")
        else:
            self.data = data

        if mask is None or isinstance(mask, GwyDataField):
            self.mask = mask
        else:
            raise TypeError("mask must be an instance of GwyDataField "
                            "or None")

        if show is None or isinstance(show, GwyDataField):
            self.show = show
        else:
            raise TypeError("show must be an instance of GwyDataField "
                            "or None")

        if point_sel is None or isinstance(point_sel, GwyPointSelection):
            self.point_selections = point_sel
        else:
            raise TypeError("point_sel must be an instance of "
                            "GwyPointSelection or None")

        if pointer_sel is None or isinstance(pointer_sel,
                                             GwyPointerSelection):
            self.pointer_selections = pointer_sel
        else:
            raise TypeError("pointer_sel must be an instance of "
                            "GwyPointerSelection or None")

        if line_sel is None or isinstance(line_sel, GwyLineSelection):
            self.line_selections = line_sel
        else:
            raise TypeError("line_sel must be an instance of "
                            "GwyLineSelection or None")

        if rectangle_sel is None or isinstance(rectangle_sel,
                                               GwyRectangleSelection):
            self.rectangle_selections = rectangle_sel
        else:
            raise TypeError("rectangle_sel must be an instance of "
                            "GwyRectangleSelection or None")

        if ellipse_sel is None or isinstance(ellipse_sel,
                                             GwyEllipseSelection):
            self.ellipse_selections = ellipse_sel
        else:
            raise TypeError("ellipse_sel must be na instance of "
                            "GwyEllipseSelection or None")

    @classmethod
    def from_gwy(cls, gwyfile, channel_id):
        """ Get channel with id=channel_id from Gwyfile object

        Args:
            gwyfile (Gwyfile): instance of Gwyfile class
            channel_id (int): id of the channel

        Returns:
            GwyChannel instance.
        """

        if not isinstance(gwyfile, Gwyfile):
            raise TypeError("gwyfile must be an instance of Gwyfile")

        title = cls._get_title(gwyfile, channel_id)
        data = cls._get_data(gwyfile, channel_id)
        visible = cls._get_visibility(gwyfile, channel_id)
        palette = cls._get_palette(gwyfile, channel_id)
        range_type = cls._get_range_type(gwyfile, channel_id)
        range_min = cls._get_range_min(gwyfile, channel_id)
        range_max = cls._get_range_max(gwyfile, channel_id)
        mask = cls._get_mask(gwyfile, channel_id)
        mask_red = cls._get_mask_red(gwyfile, channel_id)
        mask_green = cls._get_mask_green(gwyfile, channel_id)
        mask_blue = cls._get_mask_blue(gwyfile, channel_id)
        mask_alpha = cls._get_mask_alpha(gwyfile, channel_id)
        show = cls._get_show(gwyfile, channel_id)
        point_sel = cls._get_point_sel(gwyfile, channel_id)
        pointer_sel = cls._get_pointer_sel(gwyfile, channel_id)
        line_sel = cls._get_line_sel(gwyfile, channel_id)
        rectangle_sel = cls._get_rectangle_sel(gwyfile, channel_id)
        ellipse_sel = cls._get_ellipse_sel(gwyfile, channel_id)
        return GwyChannel(title=title,
                          data=data,
                          visible=visible,
                          palette=palette,
                          range_type=range_type,
                          range_min=range_min,
                          range_max=range_max,
                          mask=mask,
                          mask_red=mask_red,
                          mask_green=mask_green,
                          mask_blue=mask_blue,
                          mask_alpha=mask_alpha,
                          show=show,
                          point_sel=point_sel,
                          pointer_sel=pointer_sel,
                          line_sel=line_sel,
                          rectangle_sel=rectangle_sel,
                          ellipse_sel=ellipse_sel)

    @staticmethod
    def _get_title(gwyfile, channel_id):
        """Get title of channel with id=channel_id  from Gwyfile instance

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            title (string): Title of the channel
                            or None if title is not found

        """
        key = "/{:d}/data/title".format(channel_id)
        title = gwyfile.get_gwyitem_string(key)
        return title

    @staticmethod
    def _get_palette(gwyfile, channel_id):
        """Get name of the false color gradient used to display the channel

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            palette (string): Name of the false color gradient
                              or None if it is not defined

        """
        key = "/{:d}/base/palette".format(channel_id)
        palette = gwyfile.get_gwyitem_string(key)
        return palette

    @staticmethod
    def _get_visibility(gwyfile, channel_id):
        """ Get visibility flag for channel with id=channel_id from Gwyfile

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            visible (boolean): Visibility of the channel

        """
        key = "/{:d}/data/visible".format(channel_id)
        visible = gwyfile.get_gwyitem_bool(key)
        return visible

    @staticmethod
    def _get_range_type(gwyfile, channel_id):
        """ Get false color mapping type (as set by the Color range tool),
            the value is from GwyLayerBasicRangeType enum

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            range_type (int): false color mapping type
        """
        key = "/{:d}/base/range-type".format(channel_id)
        range_type = gwyfile.get_gwyitem_int32(key)
        return range_type

    @staticmethod
    def _get_range_min(gwyfile, channel_id):
        """ Get minimum value for user-set display range

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            range_min (double): minimum value for user-set display range
        """
        key = "/{:d}/base/min".format(channel_id)
        range_min = gwyfile.get_gwyitem_double(key)
        return range_min

    @staticmethod
    def _get_range_max(gwyfile, channel_id):
        """ Get maximum value for user-set display range

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            range_max (double): maximum value for user-set display range
        """
        key = "/{:d}/base/max".format(channel_id)
        range_max = gwyfile.get_gwyitem_double(key)
        return range_max

    @staticmethod
    def _get_mask_red(gwyfile, channel_id):
        """ Get red component of the mask color

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            mask_red (double): red component of the mask color
        """
        key = "/{:d}/mask/red".format(channel_id)
        mask_red = gwyfile.get_gwyitem_double(key)
        return mask_red

    @staticmethod
    def _get_mask_green(gwyfile, channel_id):
        """ Get green component of the mask color

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            mask_green (double): green component of the mask color
        """
        key = "/{:d}/mask/green".format(channel_id)
        mask_green = gwyfile.get_gwyitem_double(key)
        return mask_green

    @staticmethod
    def _get_mask_blue(gwyfile, channel_id):
        """ Get blue component of the mask color

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            mask_blue (double): blue component of the mask color
        """
        key = "/{:d}/mask/blue".format(channel_id)
        mask_blue = gwyfile.get_gwyitem_double(key)
        return mask_blue

    @staticmethod
    def _get_mask_alpha(gwyfile, channel_id):
        """ Get alpha (opacity) component of the mask color

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            mask_alpha (double): alpha component of the mask color
        """
        key = "/{:d}/mask/alpha".format(channel_id)
        mask_alpha = gwyfile.get_gwyitem_double(key)
        return mask_alpha

    @staticmethod
    def _get_data(gwyfile, channel_id):
        """ Get datafield from the channel with id=channel_id from Gwyfile

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            datafield (GwyDataField): channel datafield

        """

        key = "/{:d}/data".format(channel_id)
        gwydf = gwyfile.get_gwyitem_object(key)
        if gwydf:
            return GwyDataField.from_gwy(gwydf)
        else:
            raise GwyfileError(
                "Channel with id:{:d} is not found".format(channel_id))

    @staticmethod
    def _get_mask(gwyfile, channel_id):
        """ Get mask datafield from the channel with id=channel_id from Gwyfile

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
           mask (GwyDataField): mask datafield or
                                None if data item is not found

        """
        key = "/{:d}/mask".format(channel_id)
        gwymask = gwyfile.get_gwyitem_object(key)
        if gwymask:
            return GwyDataField.from_gwy(gwymask)
        else:
            return None

    @staticmethod
    def _get_show(gwyfile, channel_id):
        """ Get presentation datafield from the channel with id=channel_id
            from Gwyfile

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            show (GwyDataField): presentation datafield or
                                 None if data item is not found

        """
        key = "/{:d}/show".format(channel_id)
        gwyshow = gwyfile.get_gwyitem_object(key)
        if gwyshow:
            return GwyDataField.from_gwy(gwyshow)
        else:
            return None

    @staticmethod
    def _get_point_sel(gwyfile, channel_id):
        """Get point selections from the channel with id=channel_id

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            point_sel (GwyPointSelection): point selections or
                                           None if point selection is not found

        """
        key = "/{:d}/select/point".format(channel_id)
        gwysel = gwyfile.get_gwyitem_object(key)
        if gwysel:
            return GwyPointSelection.from_gwy(gwysel)
        else:
            return None

    @staticmethod
    def _get_pointer_sel(gwyfile, channel_id):
        """Get pointer selections from the channel with id=channel_id

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            pointer_sel (GwyPointerSelection): pointer selections or None if
                                               pointer selection is not found

        """
        key = "/{:d}/select/pointer".format(channel_id)
        gwysel = gwyfile.get_gwyitem_object(key)
        if gwysel:
            return GwyPointerSelection.from_gwy(gwysel)
        else:
            return None

    @staticmethod
    def _get_line_sel(gwyfile, channel_id):
        """Get line selections from the channel with id=channel_id

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            line_sel (GwyLineSelection): line selections or None if
                                         line selection is not found

        """
        key = "/{:d}/select/line".format(channel_id)
        gwysel = gwyfile.get_gwyitem_object(key)
        if gwysel:
            return GwyLineSelection.from_gwy(gwysel)
        else:
            return None

    @staticmethod
    def _get_rectangle_sel(gwyfile, channel_id):
        """Get rectangle selections from the channel with id=channel_id

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            rectangle_sel (GwyRectangleSelection): rectangle selection or None
                                                   if selection is not found

        """
        key = "/{:d}/select/rectangle".format(channel_id)
        gwysel = gwyfile.get_gwyitem_object(key)
        if gwysel:
            return GwyRectangleSelection.from_gwy(gwysel)
        else:
            return None

    @staticmethod
    def _get_ellipse_sel(gwyfile, channel_id):
        """Get ellipse selections from the channel with id=channel_id

        Args:
            gwyfile (Gwyfile): Gwyfile object
            channel_id (int): id of the channel

        Returns:
            ellipse_sel (GwyPointerSelection): ellipse selections or None
                                               if this selection is not found

        """
        key = "/{:d}/select/ellipse".format(channel_id)
        gwysel = gwyfile.get_gwyitem_object(key)
        if gwysel:
            return GwyEllipseSelection.from_gwy(gwysel)
        else:
            return None

    def __repr__(self):
        return "<{} instance at {}. Title: {}>".format(
            self.__class__.__name__,
            hex(id(self)),
            self.title)
