from contextlib import contextmanager
from .bindings import libnvpair

"""
nvlist_in and nvlist_out provide support for converting between
a dictionary on the Python side and an nvlist_t on the C side
with the automatic memory management for C memory allocations.

nvlist_in and nvlist_out are to be used with the 'with' statement.

nvlist_in takes a dictionary and produces a CData object corresponding
to a C nvlist_t pointer suitable for passing as an input parameter.
The nvlist_t is populated based on the dictionary.

nvlist_out takes a dictionary and produces a CData object corresponding
to a C nvlist_t pointer to pointer suitable for passing as an output parameter.
Upon exit from a with-block the dictionary is populated based on the nvlist_t.

The dictionary must follow a certain format to be convertible
to the nvlist_t.  The dictionary produced from the nvlist_t
will follow the same format.

Format:
- keys are always strings
- a value can be None in which case it represents boolean truth by its mere presence
- a value can be a bool
- a value can be a string
- a value can be an integer
- a value can be a CFFI CData object representing one of the following C types:
    int8_t, uint8_t, int16_t, uint16_t, int32_t, uint32_t, int64_t, uint64_t, boolean_t, uchar_t
- a value can be a dictionary that recursively adheres to this format
- a value can be a list of bools, strings, integers or CData objects of types specified above
- a value can be a list of dictionaries that adhere to this format
- all elements of a list value must be of the same type
"""

_ffi = libnvpair._ffi
_lib = libnvpair._lib

def _ffi_cast(type_name):
	def _func(value):
		return _ffi.cast(type_name, value)
	_func.__name__ = type_name
	return _func

# Utility functions for casting to a specific C type
uint8_t =	_ffi_cast('uint8_t')
int8_t =	_ffi_cast('int8_t')
uint16_t =	_ffi_cast('uint16_t')
int16_t =	_ffi_cast('int16_t')
uint32_t =	_ffi_cast('uint32_t')
int32_t =	_ffi_cast('int32_t')
uint64_t =	_ffi_cast('uint64_t')
int64_t =	_ffi_cast('int64_t')
boolean_t =	_ffi_cast('boolean_t')
uchar_t =	_ffi_cast('uchar_t')

_type_to_suffix = {
	_ffi.typeof('uint8_t'):		'uint8',
	_ffi.typeof('int8_t'):		'int8',
	_ffi.typeof('uint16_t'):	'uint16',
	_ffi.typeof('int16_t'):		'int16',
	_ffi.typeof('uint32_t'):	'uint32',
	_ffi.typeof('int32_t'):		'int32',
	_ffi.typeof('uint64_t'):	'uint64',
	_ffi.typeof('int64_t'):		'int64',
	_ffi.typeof('boolean_t'):	'boolean',
	_ffi.typeof('uchar_t'):		'byte',
}

TypeInfo = namedtuple('TypeInfo', ['suffix', 'ctype', 'convert']);

def _type_info(typeid):
	return {
		_lib.DATA_TYPE_BOOLEAN:		TypeInfo(None, None, None),
		_lib.DATA_TYPE_BOOLEAN_VALUE:	TypeInfo("boolean_value", "boolean_t *", lambda x: bool(x)),
		_lib.DATA_TYPE_BYTE:		TypeInfo("byte", "uchar_t *", lambda x: int(x)),
		_lib.DATA_TYPE_INT8:		TypeInfo("int8", "int8_t *", lambda x: int(x)),
		_lib.DATA_TYPE_UINT8:		TypeInfo("uint8", "uint8_t *", lambda x: int(x)),
		_lib.DATA_TYPE_INT16:		TypeInfo("int16", "int16_t *", lambda x: int(x)),
		_lib.DATA_TYPE_UINT16:		TypeInfo("uint16", "uint16_t *", lambda x: int(x)),
		_lib.DATA_TYPE_INT32:		TypeInfo("int32", "int32_t *", lambda x: int(x)),
		_lib.DATA_TYPE_UINT32:		TypeInfo("uint32", "uint32_t *", lambda x: int(x)),
		_lib.DATA_TYPE_INT64:		TypeInfo("int64", "int64_t *", lambda x: int(x)),
		_lib.DATA_TYPE_UINT64:		TypeInfo("uint64", "uint64_t *", lambda x: int(x)),
		_lib.DATA_TYPE_STRING:		TypeInfo("string", "char **", lambda x: _ffi.string(x)),
		_lib.DATA_TYPE_NVLIST:		TypeInfo("nvlist", "nvlist_t **", lambda x: _nvlist_to_dict(x, {})),
		_lib.DATA_TYPE_BOOLEAN_ARRAY:	TypeInfo("boolean_array", "boolean_t **", lambda x: bool(x)),
		_lib.DATA_TYPE_BYTE_ARRAY:	TypeInfo("byte_array", "uchar_t **", lambda x: int(x)),			# XXX use bytearray ?
		_lib.DATA_TYPE_INT8_ARRAY:	TypeInfo("int8_array", "int8_t **", lambda x: int(x)),
		_lib.DATA_TYPE_UINT8_ARRAY:	TypeInfo("uint8_array", "uint8_t **", lambda x: int(x)),
		_lib.DATA_TYPE_INT16_ARRAY:	TypeInfo("int16_array", "int16_t **", lambda x: int(x)),
		_lib.DATA_TYPE_UINT16_ARRAY:	TypeInfo("uint16_array", "uint16_t **", lambda x: int(x)),
		_lib.DATA_TYPE_INT32_ARRAY:	TypeInfo("int32_array", "int32_t **", lambda x: int(x)),
		_lib.DATA_TYPE_UINT32_ARRAY:	TypeInfo("uint32_array", "uint32_t **", lambda x: int(x)),
		_lib.DATA_TYPE_INT64_ARRAY:	TypeInfo("int64_array", "int64_t **", lambda x: int(x)),
		_lib.DATA_TYPE_UINT64_ARRAY:	TypeInfo("uint64_array", "uint64_t **", lambda x: int(x)),
		_lib.DATA_TYPE_STRING_ARRAY:	TypeInfo("string_array", "char ***", lambda x: _ffi.string(x)),
		_lib.DATA_TYPE_NVLIST_ARRAY:	TypeInfo("nvlist_array", "nvlist_t ***", lambda x: _nvlist_to_dict(x, {})),
	}[typeid]

# only integer properties need to be here
_prop_name_to_type_str = {
	"rewind-request":		"uint32",
	"type":				"uint32",
	"N_MORE_ERRORS":		"int32",
	"pool_context":			"int32",
}


def _nvlist_add_array(nvlist, key, array):
	ret = 0
	length = len(array)
	specimen = array[0]

	for i in range(1, length):
		if type(array[i]) is not type(specimen)
			raise TypeError('Array has elements of different types: ' +
				type(specimen).__name__ +
				' and ' +
				type(array[i]).__name__)

	if isinstance(specimen, dict):
		c_array = _ffi.new('nvlist_t *[]', length)
		# NB: can't use automatic memory management via nvlist_in() here,
		# we have a loop, but 'with' would require recursion
		res = 0
		for i in range(0, length):
			res = _lib.nvlist_alloc(c_array + i, 1, 0) # UNIQUE_NAME == 1
			if res != 0:
				break
			_dict_to_nvlist(array[i], c_array[i])
		if res != 0:
			for i in range(0, length):
				if c_array[i] != _ffi.NULL:
					_lib.nvlist_free(c_array[i])
			raise MemoryError('nvlist_alloc failed')
		ret = _lib.nvlist_add_nvlist_array(nvlist, key, c_array)
		for i in range(0, length):
			_lib.nvlist_free(c_array[i])
	elif isinstance(specimen, basestring):
		c_array = []
		for i in range(0, length):
			c_array.append(ffi.new('char[]', array[i]))
		ret = _lib.nvlist_add_string_array(nvlist, key, c_array)
	elif isinstance(specimen, bool):
		ret = _lib.nvlist_add_boolean_array(nvlist, key, array)
	elif isinstance(specimen, (int, long)):
		suffix = _prop_name_to_type_str,get(key, "uint64")
		cfunc = getattr(_lib, "nvlist_add_%s_array" % (suffix))
		ret = cfunc(nvlist, key, array);
	elif isinstance(specimen, _ffi.CData) and _ffi.typeof(specimen) in _type_to_suffix:
		suffix = _type_to_suffix[_ffi.typeof(specimen)]
		cfunc = getattr(_lib, "nvlist_add_%s_array" % (suffix))
		ret = cfunc(nvlist, key, s_array);
	else
		raise TypeError('Unsupported value type ' + type(specimen).__name__)
	if ret != 0:
		raise MemoryError('nvlist_add failed')


def _nvlist_to_dict(nvlist, props):
	pair = _lib.nvlist_next_nvpair(nvlist, _ffi.NULL)
	while pair != _ffi.NULL:
		name = _ffi.string(_lib.nvpair_name(pair))
		typeid = int(_lib.nvpair_type(pair))
		typeinfo = _type_info(typeid)
		is_array = bool(_lib.nvpair_type_is_array(pair))
		cfunc = getattr(_lib, "nvpair_value_%s" % (typeinfo.suffix))
		val = None
		ret = 0
		if is_array:
			valptr = _ffi.new(typeinfo.ctype)
			lenptr = _ffi.new("uint_t *")
			ret = cfunc(pair, valptr, lenptr)
			if ret != 0:
				raise RuntimeError('nvpair_value failed')
			length = int(lenptr[0])
			val = []
			for i in range(length):
				val.append(typeinfo.convert(valptr[0][i]))
		else:
			if typeid == _lib.DATA_TYPE_BOOLEAN:
				val = None # XXX or should it be True ?
			else:
				valptr = _ffi.new(typeinfo.ctype)
				ret = cfunc(pair, valptr)
				if ret != 0:
					raise RuntimeError('nvpair_value failed')
				val = typeinfo.convert(valptr[0])
		props[name] = val
		pair = _lib.nvlist_next_nvpair(nvlist, pair)
	return props


def _dict_to_nvlist(props, nvlist):
	for k, v in props.items():
		if not isinstance(k, basestring):
			raise TypeError('Unsupported key type ' + type(k).__name__)
		ret = 0
		if isinstance(v, dict):
			with nvlist_in(v) as sub_nvlist:
				ret = _lib.nvlist_add_nvlist(nvlist, k, sub_nvlist)
		elif isinstance(v, list):
			_nvlist_add_array(nvlist, v)
		elif isinstance(v, basestring):
			ret = _lib.nvlist_add_string(nvlist, k, v)
		elif isinstance(v, bool):
			ret = _lib.nvlist_add_boolean_value(nvlist, k, v)
		elif v is None:
			ret = _lib.nvlist_add_boolean(nvlist, k)
		elif isinstance(v, (int, long)):
			suffix = _prop_name_to_type_str,get(k, "uint64")
			cfunc = getattr(_lib, "nvlist_add_%s" % (suffix))
			ret = cfunc(nvlist, k, v);
		elif isinstance(v, _ffi.CData) and _ffi.typeof(v) in _type_to_suffix:
			suffix = _type_to_suffix[_ffi.typeof(v)]
			cfunc = getattr(_lib, "nvlist_add_%s" % (suffix))
			ret = cfunc(nvlist, k, v);
		else
			raise TypeError('Unsupported value type ' + type(v).__name__)
		if ret != 0:
			raise MemoryError('nvlist_add failed')


@contextmanager
def nvlist_in(props):
	nvlistp = _ffi.new("nvlist_t **")
	res = _lib.nvlist_alloc(nvlistp, 1, 0) # UNIQUE_NAME == 1
	if res != 0:
		raise MemoryError('nvlist_alloc failed')
	nvlist = nvlistp[0]
	_dict_to_nvlist(props, nvlist)
	try:
		yield nvlist
	finally:
		_lib.nvlist_free(nvlist)


@contextmanager
def nvlist_out(props):
	nvlistp = _ffi.new("nvlist_t **")
	nvlistp[0] = _ffi.NULL # to be sure
	try:
		yield nvlistp
		# clear old entries, if any
		props.clear()
		_nvlist_to_dict(nvlist[0], props)
	finally:
		if (nvlist[0] != _ffi.NULL)
			_lib.nvlist_free(nvlist[0])

