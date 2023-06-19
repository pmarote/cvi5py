# pmdb.py - classe para Gerenciamento dos Banco de Dados

import os
import sqlite3


class CviDb:
    """
    Sempre inicie CviDb e em seguida solicite db_open ou db_create
    """

    def __init__(self, db_dir, db_name):
        self.db_dir = db_dir
        self.db_name = db_name
        self.conn = None  # para guardar a conexão com o banco de dados
        self.cursor = None  # para guardar o cursor

    def opendb(self):
        db_path = os.path.join(self.db_dir, self.db_name)
        if not os.path.exists(db_path):
            raise Exception(f'O arquivo do banco de dados não foi encontrado: {db_path}')
        try:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
        except Exception as e:
            raise Exception(f'Erro ao abrir o banco de dados {db_path}: {e}')

    def createdb(self):
        db_path = os.path.join(self.db_dir, self.db_name)
        if os.path.exists(db_path):
            raise Exception(f'O arquivo do banco de dados já existe: {db_path}')
        try:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            # Aqui você poderia adicionar comandos para criar tabelas, etc.
        except Exception as e:
            raise Exception(f'Erro ao criar o banco de dados {db_path}: {e}')

    def close(self):
        self.conn.close()

    def attachdb(self, db_dir, db_name):
        db_at_name = os.path.join(db_dir, db_name)
        if not os.path.exists(db_at_name):
            raise Exception(f'O arquivo do banco de dados não foi encontrado: {db_at_name}')
        sql = f"ATTACH '{db_at_name}' AS " + db_name[:-4]
        # print(sql)
        try:
            self.exec_commit(sql)
        except Exception as e:
            raise Exception(f'Erro com attach no banco de dados {db_at_name}: {e}')
        return

    def exec_commit(self, sql: str, data=''):
        if data == '':
            self.cursor.execute(sql)
        else:
            self.cursor.execute(sql, data)
        self.conn.commit()

#    def get_all(self, sql: str):
#        self.cursor.execute(sql)
#        return self.cursor.fetchall()

    def exec_data_tirar(self, sql: str, data):
        self.cursor.execute(sql, data)
        self.conn.commit()

    def createIndex(self, database, table, field, field2=''):
        if (database == ''):
            sqldb = ''
        else:
            if (database == 'temp'):
                sqldb = f"'{database}'."
            else:
                sqldb = f"'osf{database}'."
        if field2 == '':
            sql = f"CREATE INDEX IF NOT EXISTS {sqldb}{table}_{field} ON {table} ({field} ASC);"
        else:
            sql = f"CREATE INDEX IF NOT EXISTS {sqldb}{table}_{field}_{field2} "\
                  f"ON {table} ({field} ASC, {field2} ASC);"
        print(sql)
        self.exec_commit(sql)

    def dtaSPED_AAAA_MM_DD(self, data):
        # Transforma data do formato SPED ( DDMMAAAA ) para AAAA-MM-DD
        return data[4:8] + '-' + data[2:4] + '-' + data[0:2]

    def dtaBarra_AAAA_MM_DD(self, date_str):
        day, month, year = date_str.split('/')
        return f'{year}-{month}-{day}'
