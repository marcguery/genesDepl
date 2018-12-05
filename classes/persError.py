
class dictError(Exception):
	"""Personnalised error that is iterable"""
	def __init__(self, mess):
		"""Initialize with mess as a dict only
		"""
		Exception.__init__(self)
		try:
			assert isinstance(mess, dict)
			self.message = mess
		except AssertionError:
			mess="dictError must be initialize with dict only"
			raise TypeError(mess)

	def __getitem__(self, item):
		return self.message[item]