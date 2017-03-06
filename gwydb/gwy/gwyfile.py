""" Wrapper for GwyfileObject from Libgwyfile C library

    Classes:
        GwyfileError(Exception): Exceptions during operations with gwy files
        GwyfileErrorCMsg(GwyfileError): Libgwyfile C library exceptions
        Gwyfile: representation of GwyfileObject* from Libgwyfile C library

"""
import os.path

from gwydb.gwy._libgwyfile import ffi, lib


class GwyfileError(Exception):
    """
    Exceptions during operations with gwy files
    """

    pass


class GwyfileErrorCMsg(GwyfileError):
    """
    Class for libgwyfile C library exceptions
    """

    def __init__(self, c_error_msg):
        if c_error_msg:
            error_msg = ffi.string(c_error_msg).decode('utf-8')
            super().__init__(error_msg)
        else:
            super().__init__()


class Gwyfile:
    """Wrapper class for GwyfileObject from Libgwyfile C library

    Attributes:
        c_gwyfile (cdata  GwyfileObject*): gwyfile object from
                                           Libgwyfile C library
        filename ('string'): name of the file

    Methods:
        check_gwyobject(key):  Check presence of object in the gwyfile
        get_gwyobject(key):    Get Gwyfile object
        get_gwyitem_bool(item): Get boolean value contained in Gwy data item
        get_gwyitem_double(item): Get double value contained in Gwy data item
        get_gwyitem_int32(item): Get 32bit integer value contained in
                                 Gwy data item
        get_gwyitem_string(item): Get string value contained in Gyw data item
    """

    def __init__(self, c_gwyfile, basename):
        """
        Args:
            c_gwyfile (cdata GwyfileOjbect*): gwyfile object from
                                              Libgwyfile C library
            basename (string): name of file without path
                               (e.g. 'sample.gwy' for 'data/sample.gwy')

        The top-level object of the c_gwyfile must be 'GwyContainer'
        """

        if not c_gwyfile:
            raise GwyfileError("c_gwyfile object is empty")

        c_toplevel_object_name = lib.gwyfile_object_name(c_gwyfile)
        if c_toplevel_object_name:
            toplevel_object_name = ffi.string(c_toplevel_object_name)
        else:
            error_msg = 'The top-level object of c_gwyfile is empty'
            raise GwyfileError(error_msg)

        if not toplevel_object_name == b'GwyContainer':
            error_msg = 'The top-level object of c_gwyfile is not ' \
                        ' a GwyContainer'
            raise GwyfileError(error_msg)

        self.c_gwyfile = c_gwyfile
        self.filename = basename

    def _get_gwyitem_value(self, item_key, cfunc):
        """Get value (in C representation) contained in Gwy data item

        Args:
            item_key (string): Name of the Gwy data item
            cfunc (<C function>): C func. to get the value of this type
                                  (e.g. lib.gwyfile_item_get_string)

        Returns:
            value: value of the Gwy data item in C representation or None
                   if Gwy data item is None

        """
        item = lib.gwyfile_object_get(self.c_gwyfile, item_key.encode('utf-8'))

        if item:
            value = cfunc(item)
            return value
        else:
            return None

    def get_gwyitem_bool(self, item_key):
        """Get boolean value contained in Gwy data item

        Args:
            item_key (string): Name of the Gwy data item

        Returns:
            boolean: True if gwyitem exists and its value is True,
                     otherwise False

        """
        cfunc = lib.gwyfile_item_get_bool
        cvalue = self._get_gwyitem_value(item_key, cfunc)
        if cvalue:
            return True
        else:
            return False

    def get_gwyitem_string(self, item_key):
        """Get string value contained in Gwy data item

        Args:
            item_key (string): Name of the Gwy data item

        Returns:
            string: The string contained in Gwy data item
                    or None if item is not found

        """
        cfunc = lib.gwyfile_item_get_string
        cvalue = self._get_gwyitem_value(item_key, cfunc)
        if cvalue:
            return ffi.string(cvalue).decode('utf-8')
        else:
            return None

    def get_gwyitem_object(self, item_key):
        """Get the object value contained in a Gwy data item

        Args:
            item_key (string): Name of the Gwy data item

        Returns:
            item (cdata GwyfileObject*): The object value of item.
                                         Or None if item is not found

        """
        cfunc = lib.gwyfile_item_get_object
        gwyobject = self._get_gwyitem_value(item_key, cfunc)
        if gwyobject:
            return gwyobject
        else:
            return None

    def get_gwyitem_int32(self, item_key):
        """Get the 32bit integer value contained in a Gwy file data item

        Args:
            item_key (string): Name of the Gwy data item

        Returns:
            value (int): The integer contained in Gwy data item
                         or None if the item is not found
        """
        cfunc = lib.gwyfile_item_get_int32
        value = self._get_gwyitem_value(item_key, cfunc)
        return value

    def get_gwyitem_double(self, item_key):
        """Get the double value contained in a Gwy file data item

        Args:
            item_key (string): Name of the Gwy data item

        Returns:
            value (double): The double value contained in Gwy data item
                            or None if the item is not found
        """
        cfunc = lib.gwyfile_item_get_double
        value = self._get_gwyitem_value(item_key, cfunc)
        return value

    @staticmethod
    def from_gwy(filename):
        """Create Gwyfile instance from file

        Args:
            filename (string): filename including path

        Returns:
            Gwyfile:
                instnce of Gwyfile class

        """
        error = ffi.new("GwyfileError*")
        errorp = ffi.new("GwyfileError**", error)

        if not os.path.isfile(filename):
            raise OSError("Cannot find file {}".format(filename))

        c_gwyfile = lib.gwyfile_read_file(filename.encode('utf-8'), errorp)

        if not c_gwyfile:
            raise GwyfileErrorCMsg(errorp[0].message)

        basename = os.path.basename(filename)

        gwyfile = Gwyfile(c_gwyfile, basename)
        return gwyfile
