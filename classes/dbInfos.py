import os

class DataBase(object):
	"""Initialize a DataBase object with all the informations needed
	location : repository of the database(s)
	dbtype : Type of database to use
	log : path to log file
	detail : path for JSON parsed details
		here is a template:
		{
			"sql":{
				"pers":
					{
						"login": "YOURLOGIN",
						"password": "YOURPW"
					},
				"base":
					{
						"host": "HOST",
						"database": "DBNAME"
					}
			},
			"sqlite":
			{
				"database":"DBNAME.sqlite"
			}
		}
	"""
	def __init__(self):
		"""Change the values to fit your database here
		"""
		self.location = "data/"
		self.dbtype = "sqlite"
		self.log = "log/last-mod.txt"
		self.detail = "details.json"
	@property
	def date(self):
		"""Return the date of last modification of the log
		"""
		try:
			return os.path.getmtime(self.log)
		except:
			mess="Le fichier log est introuvable."
			raise FileNotFoundError(mess)

	def change(self, loc=None, dbtype=None, log=None, detail=None):
		self.location = loc if loc is not None else self.location
		self.dbtype = dbtype if dbtype is not None else self.dbtype
		self.log = log if log is not None else self.log
		self.detail = detail if detail is not None else self.detail