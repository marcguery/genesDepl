
class dictError(Exception):
	"""docstring for ClassName"""
	def __init__(self, mess):
		super(Exception, self).__init__()
		self.message = mess
	def __repr__(self):
		return self.message
	def __getitem__(self, item):
         return self.message[item]