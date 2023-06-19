<?php


class CvSqlite {

    protected $db3;         // db3 file name
    protected $db3_table;   // name of the table current converting
    public    $db;          // Sqlite3 object
    
    protected $filename;    // ver __construct
    protected $cvh;         // ver __construct

    public function __construct($filename = null, $cvh = null, $db3 = null)
    // se quiser abrir dentro de CVI_RESULT . "/{$this->db3}.db3", preencher só com $db3
            // exemplo original: se o db é txt, vai abrir dentro de CVI_RESULT, trazendo também o CNPJ, o txt.db3 
    // se quiser abrir fora de CVI_RESULT, especialmente, utilizar $filename
    // essa coisa de vir $cvh ainda não usei aqui, mas eu sempre utilizava na versão web de cvi
    {
        if (! is_null($filename) ) $this->filename = $filename;
            else $this->filename = null;
        if (! is_null($cvh) ) $this->cvh = $cvh;
            else $this->cvh = null;
        //if (is_null($db3)) $this->db3 = 'txt';
        if (! is_null($db3) ) $this->db3 = $db3;
            else $this->db3 = null;
        $this->db3Open();
        //$this->txtRead();
    }

    public function db3Open() 
    {
         $db3Name = CVI_RESULT . "/{$this->db3}.db3";
         if (! is_null($this->filename) ) $db3Name = $this->filename;
         if (!file_exists($db3Name)) { 
            if ($this->db = new \SQLite3($db3Name)) {
            } else {
                h_werro_die("Falha ao criar Banco de Dados {$db3Name}");
            }  
            $this->db->query('PRAGMA encoding = "UTF-8";');
        } else {
            if ($this->db = new \SQLite3($db3Name)) {
            } else {
                h_werro_die("Falha ao abrir Banco de Dados {$db3Name}");
            }  
        }
    }
    
    public function db3Attach($db3) {
        // ###
        // ###TODO### POR ENQUANTO NÂO ESTÀ USANDO $filename
        // ###
        $arqdb = CVI_RESULT . "/{$db3}.db3";
        if ($this->exec("ATTACH '{$arqdb}' AS " . basename($db3))) {
        } else {
                h_werro_die("Falha ao abrir (attach) Banco de Dados '{$arqdb}' AS {$db3}");
        }
    }

    public function createTableFromSqlsrv($adoDb, $dbname, $tablename) {

        // capturando os campos e tipos
        $sql = <<<EOD
SELECT sTYP.name AS system_type_name, sCOL.name AS name FROM {$dbname}.sys.columns AS sCOL
INNER JOIN {$dbname}.sys.types AS sTYP ON sTYP.system_type_id = sCOL.system_type_id
WHERE object_id = OBJECT_ID('{$dbname}.{$tablename}') AND sTYP.system_type_id = sTYP.user_type_id
ORDER BY column_id
EOD;
        //h_log($sql);
        $adoDb->execute($sql);

        $campos = '';
        $tp_campos = '';
        $fields = array();
        while (!$adoDb->rs->EOF) {
            $noLines = false;   // TODO
            $adoDb->getLine();
            // por algum motivo, pode haver duplicação de nome de campos, talvez ao tirar ou limpar caracteres especiais
            $campo = str_replace("\r", '', str_replace("\n", '_', str_replace("/", '_', str_replace(" ", '_', str_replace("(", '_', str_replace(")", '_', str_replace("-", '_', utf8_encode($adoDb->rsData[1])))))))); // assegura que não tem mudança de linha, nem caracteres ruins no Sqlite
            while (isset($fields[$campo])) $campo .= '_';
            $fields[$campo] = $campo;
            $campos .= ($campos == '' ? '' : "\t") . $campo;
            $tp_campos .= ($tp_campos == '' ? '' : "\t") . "{$adoDb->rsData[0]}#" . $adoDb->fieldTypesSqlsrvToSqlite($adoDb->rsData[0]);
            $adoDb->rs->MoveNext(); 
        }
        //$adoDb->db->close();

        $this->db3_table = (mb_strpos($dbname, 'DocAtrib') !== False ? 'DocAtrib' : (mb_strpos($dbname, 'Dfe') !== False ? 'Dfe' : '')) . '_' . str_replace('[', '', str_replace(']', '', str_replace('.', '_', $tablename)));
        $this->db3TableCreate($campos, $tp_campos);
        return $this->db3_table;
    }



    public function insertFromSqlsrv($adoDb, $sql, $db3_table = Null) {

        $this->db3_table = $db3_table;       

        $cells = 0;
        $noLines = true;

        $adoDb->execute($sql);

        $this->db->exec('BEGIN;');     // Conforme faq do Sqlite, acelera Insert (questao 19)
        while (!$adoDb->rs->EOF) {
            $noLines = false;   // TODO
            $adoDb->getLine();

            $insert_query = "INSERT INTO {$this->db3_table} VALUES( ";
            foreach($adoDb->rsData as $key => $value) {
                $value = $this->db->escapeString(utf8_encode($value));
                $columnType = $adoDb->fieldTypesSqlite[$key];
                // se o campo tiver zero ou mais que 25 caracteres, grava como string, ou melhor, entre aspas. Senão, se INT ou REAL, grava sem aspas
                if(mb_strlen($value) > 0 && mb_strlen($value) < 25 && ($columnType == 1 || $columnType == 2)) $insert_query .= str_replace(',','.',str_replace('.', '', trim($value))) . ", ";
                else $insert_query .= "'{$value}', ";
                $cells++;
            }
            $insert_query = substr($insert_query, 0, -2) . ' );';
            //h_log("{$insert_query}\r\n");
            //$this->db->query($insert_query);
            @$status = $this->db->exec($insert_query);
            if ($status === False) h_log("##ERROR## Sql error when trying to sqlite exec #{$insert_query}#\nSQLite error msg: " . $this->db->lastErrorMsg() . "\n");

            if ($cells > 250000) {
                $cells = 0;
                $this->db->exec('COMMIT;'); // Conforme faq do Sqlite, acelera Insert (questao 19)
                h_wecho('*');
                $this->db->exec('BEGIN;');     // Conforme faq do Sqlite, acelera Insert (questao 19)
            }
            $adoDb->rs->MoveNext(); 
        }
        $this->db->exec('COMMIT;'); // Conforme faq do Sqlite, acelera Insert (questao 19)
        h_wecho("Tabela gerada com sucesso!\n");
    }
   
    protected function db3TableCreate($campos, $tp_campos) {

        h_wecho("Campos: {$campos}\nTpCampos: {$tp_campos}\n");
        $aCampos = explode("\t", $campos);
        $aTpCampos = explode("\t", $tp_campos);
        // criação da tabela. Definição completa dos campos, tentando inclusive descobrir se o campo é Texto, Real ou Int
        $sql_create = "CREATE TABLE IF NOT EXISTS {$this->db3_table} (";
        foreach($aCampos as $indice => $valor) {
            $aTpCampo = explode('#', $aTpCampos[$indice]);
            $tipo_campo = $aTpCampo[1];
            $sql_create .= $valor; 
            $sql_create .= ($tipo_campo == 1 ? ' INT' : ($tipo_campo == 2 ? ' REAL' : ($tipo_campo == 3 ? ' TEXT' : ' BLOB'))) . ", ";
        }
        $sql_create = substr($sql_create, 0, -2) . ');';
        //h_wecho("#sql_create: {$sql_create}#\n");
        $this->exec($sql_create);
    }

    /**
     * controlled sqlite query, please don't use cvidb->db->query
     */
    public function query($querystr, $echo = true) 
    {
        if ($echo) h_wecho("[" . date("H:i:s") . "]CvSqlite query: #{$querystr}#\r\n");
        return $this->db->query($querystr);
    }

    /**
     * controlled sqlite escapeString, please don't use cvidb->db->escapeString
     */
    public function escapeString($value) 
    {
        return $this->db->escapeString($value);
    }
    /**
     * controlled sqlite exec, please don't use cvidb->db->exec
     */
    public function exec($execstr, $echo = true) 
    {
        if ($echo) h_wecho("[" . date("H:i:s") . "]CvSqlite exec: #{$execstr}#\r\n");
        @$status = $this->db->exec($execstr);
        if ($status === False) h_werro_die("##ERROR## Sql error when trying to sqlite exec #{$execstr}#\nSQLite error msg: " . $this->db->lastErrorMsg() . "\n");
        return $status;
    }

    /**
     * controlled sqlite prepare, please don't use cvidb->db->prepare
     */
    public function prepare($preparestr) 
    {
        @$status = $this->db->prepare($preparestr);
        if ($status === False) h_werro_die("##ERROR## Sql error when trying to sqlite prepare #{$preparestr}#\nSQLite error msg: " . $this->db->lastErrorMsg() . "\n");
        return $status;
    }

    /**
     * query a SQL and return to an array
     */
    public function sqlToArray($sql) {
        // don't forget to test, after using, if count(array) > 0... 
        @$res = $this->query($sql);
        if ($res === False) h_werro_die("##ERROR## Sql error when trying to sqlite query #{$sql}#\nSQLite error msg: " . $this->db->lastErrorMsg() . "\n");
        $a_res = array();
        while ($param = $res->fetchArray(SQLITE3_ASSOC)) {
            $a_res[] = $param;
        }
        return $a_res;
    }

    public function createTableFromSql($table, $sql) {
        $sqlDrop = <<<EOD
DROP TABLE IF EXISTS {$table}
EOD;
        $this->exec($sqlDrop);
        //h_wecho("Dropped table (if exists) {$table}\n");
        $sqlCreate = <<<EOD
CREATE TABLE {$table} AS
{$sql}
EOD;
        //h_log($sqlCreate);
        $this->exec($sqlCreate);
        //h_wecho("Created table {$table} from sql\n");
    }

    public function createTempTableFromSql($table, $sql) {
        $sqlDrop = <<<EOD
DROP TABLE IF EXISTS {$table}
EOD;
        $this->exec($sqlDrop);
        //h_wecho("Dropped table (if exists) {$table}\n");
        $sqlCreate = <<<EOD
CREATE TEMP TABLE {$table} AS
{$sql}
EOD;
        //h_log($sqlCreate);
        $this->exec($sqlCreate);
        //h_wecho("Created table {$table} from sql\n");
    }

    public function insertIntoTableFromSql($CTsql, $table, $sql) {
        //h_log($CTsql);
        $sqlDrop = <<<EOD
DROP TABLE IF EXISTS {$table}
EOD;
        $this->exec($sqlDrop);
        //h_wecho("Dropped table (if exists) {$table}\n");
        $this->exec($CTsql);
        //h_wecho("Created table {$table} from sql\n");
        $sqlInsert = <<<EOD
INSERT INTO {$table}
{$sql}
EOD;
        //h_log($sqlInsert);
        $this->exec($sqlInsert);
        //h_wecho("Inserted data into table {$table} from sql\n");
    }

    public function createIndex($database, $table, $field, $field2 = null) {
        if ($database == '') $sqldb = '';
        else {
            if ($database == 'temp') $sqldb = "'{$database}'.";
            else                     $sqldb = "'osf{$database}'.";
        }
        if (is_null($field2)) $this->exec("CREATE INDEX IF NOT EXISTS {$sqldb}{$table}_{$field} ON {$table} ({$field} ASC);");
        else $this->exec("CREATE INDEX IF NOT EXISTS {$sqldb}{$table}_{$field}_{$field2} ON {$table} ({$field} ASC, {$field2} ASC);");
    }
    
    public function createUniqueIndex($database, $table, $field, $field2 = null) {
        // a ideia é fazer em duas etapas permitindo que haja o index e depois seja detectado se houve duplicidades
        // é estranho, mas pode ajudar nas auditorias
        $this->createIndex($database, $table, $field, $field2);
        if (is_null($field2)) $sql = "SELECT max(qtd) AS rept FROM (SELECT count({$field}) AS qtd FROM {$table} GROUP BY {$field});";
        else $sql = "SELECT max(qtd) AS rept FROM (SELECT count({$field2}) AS qtd FROM {$table} GROUP BY {$field}, {$field2});";
        $a_res = $this->sqlToArray($sql);
        if ($a_res[0]['rept'] > 1) {
            $errormsg = "##Erro## ! Houve duplicidade de {$field}" . (is_null($field2) ? '' : ", {$field2}"). " em {$table} ! Qtd = {$a_res[0]['rept']}\nSQL=\n{$sql}\n";
            h_log($errormsg);
            $sql = "SELECT min(rowid) AS minrowid FROM {$table};";
            $a_res = $this->sqlToArray($sql);
            h_log("{$sql} Mínimo rowid: {$a_res[0]['minrowid']}\n");
            $sql = "SELECT max(rowid) AS maxrowid FROM {$table};";
            $a_res = $this->sqlToArray($sql);
            h_log("{$sql} Máximo rowid: {$a_res[0]['maxrowid']}\n");
            //h_log("Proposta de Delete:\nDELETE FROM {$table} WHERE rowid >= " . $a_res[0]['maxrowid'] / 2 + 1 . ";\n");
            $sql = "DELETE FROM {$table} WHERE rowid >= " . ($a_res[0]['maxrowid'] / 2 + 1) . ";\n";
            h_log("Proposta de Delete:\n{$sql}\n");
            $this->exec($sql);
            h_werro($errormsg . "\nFiz um Delete from, vamos ver se corrige para a próxima.\nVerifique tudo em h_log.log");
        }
    }


    /**
     * create table com .txt file, separated by tabs, need to be in utf format
     */
    public function insertIntoTableFromTxt($txt_file, $tablename, $cabec = True) {

        $dados = file_get_contents($txt_file);
        $linhas = explode("\n", $dados);
        $this->exec('BEGIN;'); // Conforme faq do Sqlite, acelera Insert (questao 19)
        foreach($linhas as $key => $value) {
            // Se $cabec = True é porque há linha de cabeçalho, que deve ser pulada!
            if ($cabec) {
                $cabec = False;
                continue;
            }
            // usually last line is empty... jump all empty lines
            if (trim($value, " \n\r") === '') continue;

            $campos = explode("\t", trim($value, " \n\r"));
            $insert_query = "INSERT INTO {$tablename} VALUES( ";
            foreach($campos as $keyc => $valuec) $insert_query .= "'" . $this->db->escapeString($valuec) . "', ";
            $insert_query = substr($insert_query, 0, -2) . ')';
            $this->exec($insert_query, false);
        }
        $this->exec('COMMIT;'); // Conforme faq do Sqlite, acelera Insert (questao 19)
    }

    public function db_lista_campos($tabela) {
        $valor = array();
        $result = $this->db->query("PRAGMA table_info(`{$tabela}`);");
        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $valor[] = $row['name'];
        }
        return $valor;
    }

    public function db_lista_tabelas() {
        $valor = array();
        $result = $this->db->query("SELECT name FROM sqlite_master WHERE type='table';");
        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $valor[] = $row['name'];
        }
        return $valor;
    }

    public function db_lista_dbs() {
        $valor = array();
        $result = $this->db->query("PRAGMA database_list;");
        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $valor[] = $row;
        }
        return $valor;
    }

}

