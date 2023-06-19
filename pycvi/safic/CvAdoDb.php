<?php


class AdoDb {

    public $db;                     // objeto AdoDb
    public $dsn;
    public $rs;                     // objeto RecordSet

    protected $firstLine;           // to control whether an Sql just ocurred, to retrieve field attributes
    public $line;
    
    public $pipeName;
    public $state;

    // preenchidos em AdoDb::getLine()
    public $rsData;              // Valores de uma linha de RecordSet
    public $fieldNames;
    public $fieldTypes;
    public $fieldTypesSqlite;


    public function __construct()
    {
    }

    public function info() 
    {
        $uniqid = date("ymd") . uniqid();
        $tmpFile = str_replace("/", "\\", CVI_TMP) . "\\sqldbi{$uniqid}.txt";
        $cmd = "sqllocaldb i SaficV150 > {$tmpFile}";
        $WshShell = new COM("WScript.Shell");
        $oExec = $WshShell->Run("cmd /C {$cmd}", 0, false);
        unset($WshShell);
        
        $i = 0;
        while (!file_exists($tmpFile)) {
            $i++;
            sleep(1);
            clearstatcache();
        }
        
        $sld_text = file_get_contents($tmpFile);
        // h_log($sld_text);
        $this->pipeName = trim( mb_substr($sld_text, mb_strpos($sld_text, 'Instance pipe name:') + 20) );
        $this->state = trim( mb_substr($sld_text, mb_strpos($sld_text, 'State:') + 20, 7));
        unlink($tmpFile);
        if (!($this->state == 'Running' || $this->state == 'Stopped')) {
            $this->state = 'Unavailable';
            $this->pipeName = null;
        }
        return $tmpFile . "#" . $i . "#" . $sld_text;

    }

    public function open() 
    {
        $serverName = '{' . $this->pipeName . '};Database={master};Trusted_Connection={True};';
        $this->db = new COM("ADODB.Connection"); 
        $dsn = 'DRIVER={SQL Server};SERVER=' . $serverName . '';
        return $this->db->Open($dsn);
    }

    public function timeExecute($sql) { // este é mais para comandos como ALTER TABLE, que não trazem resultados e é interessante medir o tempo 
        $startTime = microtime(true);
        $this->db->Execute($sql);
        $this->firstLine = True;
        //h_wecho("SQL executado: {$sql} em " . (microtime(true) - $startTime) . " segundos\n");
        h_wecho("SQL executado: {$sql} em " . number_format((microtime(true) - $startTime), 3, ',', '.') . " segundos\n");
    }
    
    public function execute($sql) { 
        $this->rs = $this->db->Execute($sql);
        $this->firstLine = True;
    }
    
    public function getLine($utf8 = false) {
        // por padrão (razões históricas), retorna em ANSI   Por isso, acima $utf8 = false
        $this->rsData = array();
        if ($this->firstLine) {
            $this->fieldNames = array();
            $this->fieldTypes = array();
            $this->fieldTypesSqlite = array();
            for($i=0; $i<$this->rs->Fields->Count; $i++) {
                $this->fieldNames[] = $this->rs->Fields[$i]->Name;
//                h_wecho($this->rs->Fields[$i]->Name."#");
            }
//            h_wecho("\n");
            for($i=0; $i<$this->rs->Fields->Count; $i++) {
                $this->fieldTypes[] = $this->rs->Fields[$i]->Type;
                $this->fieldTypesSqlite[] = $this->typeAdjustSqlite($this->rs->Fields[$i]->Type);
//                h_wecho($this->rs->Fields[$i]->Type."#");
            }
//            h_wecho("\n");
            $this->firstLine = False;
        }        
        for($i=0; $i<$this->rs->Fields->Count; $i++) {
            if ($utf8)  $this->rsData[] = utf8_encode($this->rs->Fields[$i]->Value);
            else        $this->rsData[] = $this->rs->Fields[$i]->Value;
//            h_wecho($this->rs->Fields[$i]->Value."#");
        }  
    }

    public function createTableFromSql($table, $sql) {
        $sqlDrop = <<<EOD
DROP TABLE IF EXISTS {$table}
EOD;
        $this->db->Execute($sqlDrop);
        h_wecho("Dropped table (if exists) {$table}\n");
        $this->db->Execute("EXEC sp_configure 'remote query timeout', 0");
        $sqlCreate = <<<EOD
SELECT csqA.* INTO {$table} FROM
( {$sql} ) AS csqA
EOD;
        //h_log($sqlCreate);
        $this->db->Execute($sqlCreate);
        h_wecho("Created table {$table} from sql\n");
    }

    
    public function insertIntoTableFromSql($CTsql, $table, $sql) {
        $sqlDrop = <<<EOD
DROP TABLE IF EXISTS {$table}
EOD;
        $this->db->Execute($sqlDrop);
        h_wecho("Dropped table (if exists) {$table}\n");
        //h_log($CTsql);
        $this->db->Execute($CTsql);
        h_wecho("Created table {$table} from sql\n");
        $sqlInsert = <<<EOD
INSERT INTO {$table}
{$sql}
EOD;
        //h_log($sqlInsert);
        $this->db->Execute($sqlInsert);
        h_wecho("Inserted data into table {$table} from sql\n");
    }
    

    
    public function typeAdjustSqlite($sqlsrvType) {
        // listegem completa em https://www.w3schools.com/asp/prop_field_type.asp
        // ($columnType == 1 ? 'INT' : ($columnType == 2 ? 'REAL' : ($columnType == 3 ? 'TEXT' : ($columnType == 4 ? 'BLOB' : 'NULL'))));
        $aInt = [2, 3, 11, 16, 17, 18, 19, 20, 21, 128, 136, 204, 205];
        $aReal = [4, 5, 6, 14, 64, 131, 139];
        $aText = [7, 8, 72, 129, 130, 132, 133, 135, 138, 200, 201, 202, 203];
        $aBlobNull = [0, 9, 10, 12, 13];
        $sqliteType = -$sqlsrvType;
        if (in_array($sqlsrvType, $aInt)) $sqliteType = 1;
        if (in_array($sqlsrvType, $aReal)) $sqliteType = 2;
        if (in_array($sqlsrvType, $aText)) $sqliteType = 3;
        if (in_array($sqlsrvType, $aBlobNull)) $sqliteType = 4;
        return $sqliteType;
    }

    public function fieldTypesSqlsrvToSqlite($sqlsrvType) {
        // ($columnType == 1 ? 'INT' : ($columnType == 2 ? 'REAL' : ($columnType == 3 ? 'TEXT' : ($columnType == 4 ? 'BLOB' : 'NULL'))));
        $aInt = ['tinyint', 'smallint', 'int', 'bit', 'bigint'];
        $aReal = ['real', 'money', 'float', 'decimal', 'numeric', 'smallmoney'];
        $aText = ['text', 'uniqueidentifier', 'date', 'time', 'datetime2', 'datetimeoffset', 'smalldatetime', 'datetime', 'sql_variant', 'ntext', 'varbinary', 'binary', 'varchar', 'char', 'timestamp', 'sysname', 'nvarchar', 'nchar', 'geography', 'geometry', 'hierarchyid', 'xml'];
        $aBlobNull = ['image'];
        $sqliteType = 'ERRO';
        if (in_array($sqlsrvType, $aInt)) $sqliteType = 1;
        if (in_array($sqlsrvType, $aReal)) $sqliteType = 2;
        if (in_array($sqlsrvType, $aText)) $sqliteType = 3;
        if (in_array($sqlsrvType, $aBlobNull)) $sqliteType = 4;
        if ($sqliteType == 'ERRO') h_erro_die("##ERRO FATAL## Não consegui converter o sqlsrvType {$sqlsrvType} em AdoDb::fieldTypesSqlsrvToSqlite");
        return $sqliteType;
    }

    /**
     * create table com .txt file, separated by tabs, utf format text required
     */
    public function insertIntoTableFromTxt($txt_file, $tablename, $cabec = True) {

        $txt_encoding = 'UTF-8';
        $dados = file_get_contents($txt_file);
        $linhas = explode("\n", $dados);
        //$this->exec('BEGIN;'); // Conforme faq do Sqlite, acelera Insert (questao 19)
        foreach($linhas as $key => $value) {
            // Se $cabec = True é porque há linha de cabeçalho, que deve ser pulada!
            if ($cabec) {
                $cabec = False;
                continue;
            }
            // usually last line is empty... jump all empty lines
            if (trim($value, " \n\r") === '') continue;

            if (mb_detect_encoding($value, 'UTF-8', true)) $this->txt_encoding = 'UTF-8';
            else $this->txt_encoding = 'ANSI';
            if ($this->txt_encoding == 'UTF-8') $value = utf8_decode($value);

            $campos = explode("\t", trim($value, " \n\r"));
            $insertSql = "INSERT INTO {$tablename} VALUES( ";
            foreach($campos as $keyc => $valuec) $insertSql .= "'" . addslashes($valuec) . "', ";
            $insertSql = substr($insertSql, 0, -2) . ')';
            $this->db->Execute($insertSql);
        }
        //$this->exec('COMMIT;'); // Conforme faq do Sqlite, acelera Insert (questao 19)
    }

}

