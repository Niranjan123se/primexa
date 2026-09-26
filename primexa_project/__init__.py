# Enable PyMySQL fallback for cPanel MySQL database connections
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

