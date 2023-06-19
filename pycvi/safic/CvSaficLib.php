<?php


class CvSaficLib {
    
    public $databases;      // database list
    public $sfdb;           // lista dos dbs conforme estrutura Safi para a OSF em uso, preenchida em CvSaficLib::getDatabasesOsf
    public $aGetOsfList;    // um array com dados gerais das OSFs disponíveis, para consultas gerais
    
    public $osf = Null;         // opções a serem preenchidas em CvSaficLib::optDialog()
    public $maxCells = Null;
    public $setToDataType = Null;
    public $nivelDetalhe = Null;
    public $valMin = Null;
    public $opt4Sel = Null;

    public function __construct() {
    }

    protected function loadLastData() {
        $arqData =  CVI_LOG . "/CvSaficLib.dat";
        if (!file_exists($arqData)) return false;
        $a_vars = file_get_contents($arqData);
        if ($a_vars === false) {
            $erro_msg = "##FATAL ERROR... {$arqData} not readable\n";
            h_werro_die($erro_msg);
        }
        $a_vars = unserialize($a_vars);
        $this->osf = $a_vars[0];
    }

    protected function saveLastData() {
        $arqData =  CVI_LOG . "/CvSaficLib.dat";
        if (file_exists($arqData)) unlink($arqData);
        file_put_contents($arqData, serialize(array($this->osf)));
    }



    public function optDialog($title, $osfList, $opt4lbl = Null, $opt4field = Null, $showMaxCells = True, $showSetToDataType = True, $showNivelDetalhe = True, $showValMin = True) {
        $this->loadLastData();

        $dialog = new GtkDialog($title, null, Gtk::DIALOG_MODAL);
        $dialog->set_position(Gtk::WIN_POS_CENTER_ALWAYS);
        $vsize = 150;
        if ($showMaxCells)      $vsize += 80; 
        if ($showSetToDataType) $vsize += 80;
        if ($showNivelDetalhe)  $vsize += 80;
        $dialog->set_default_size(150, $vsize);

        $lbl_1 	= new GtkLabel("Selecione a OSF:");

        $combobox = new GtkComboBox();  // Create a combobox
        if (defined("GObject::TYPE_STRING")) {  // Create a model
            $model = new GtkListStore(GObject::TYPE_STRING);
        } else {
            $model = new GtkListStore(Gtk::TYPE_STRING);
        }
        $combobox->set_model($model);   // Set up the combobox
        $cellrenderer = new GtkCellRendererText();
        $combobox->pack_start($cellrenderer);
        $combobox->set_attributes($cellrenderer, 'text', 0);
        $i = 0; $active = 0;
        foreach($osfList as $choice) {     // Stuff the choices in the model
            $model->append(array($choice));
            //h_wecho("#@{$choice}@#!{$this->osf}!#");
            if (mb_substr($choice, 0, 11) == $this->osf) $active = $i;
            $i++;
        }
        $combobox->set_active($active);

        $lbl_2 	= new GtkLabel("Quantidade de Células:");
        $combobox2 = new GtkComboBox();  // Create a combobox
        if (defined("GObject::TYPE_STRING")) {  // Create a model
            $model2 = new GtkListStore(GObject::TYPE_STRING);
        } else {
            $model2 = new GtkListStore(Gtk::TYPE_STRING);
        }
        $combobox2->set_model($model2);   // Set up the combobox
        $cellrenderer2 = new GtkCellRendererText();
        $combobox2->pack_start($cellrenderer2);
        $combobox2->set_attributes($cellrenderer2, 'text', 0);
        $alist = [1000, 10000, 100000, 1000000, "Ilimitado (Somente .txt)"];
        foreach($alist as $choice) {     // Stuff the choices in the model
            $model2->append(array($choice));
        }
        $combobox2->set_active(0);
        
        $lbl_3 	= new GtkLabel("Exportando para:");
        $combobox3 = new GtkComboBox();  // Create a combobox
        if (defined("GObject::TYPE_STRING")) {  // Create a model
            $model3 = new GtkListStore(GObject::TYPE_STRING);
        } else {
            $model3 = new GtkListStore(Gtk::TYPE_STRING);
        }
        $combobox3->set_model($model3);   // Set up the combobox
        $cellrenderer3 = new GtkCellRendererText();
        $combobox3->pack_start($cellrenderer3);
        $combobox3->set_attributes($cellrenderer3, 'text', 0);
        $alist = ['html', 'txt'];
        foreach($alist as $choice) {     // Stuff the choices in the model
            $model3->append(array($choice));
        }
        $combobox3->set_active(0);

        $lbl_5 	= new GtkLabel("Nível de Detalhe:");
        $combobox5 = new GtkComboBox();  // Create a combobox
        if (defined("GObject::TYPE_STRING")) {  // Create a model
            $model5 = new GtkListStore(GObject::TYPE_STRING);
        } else {
            $model5 = new GtkListStore(Gtk::TYPE_STRING);
        }
        $combobox5->set_model($model5);   // Set up the combobox
        $cellrenderer5 = new GtkCellRendererText();
        $combobox5->pack_start($cellrenderer5);
        $combobox5->set_attributes($cellrenderer5, 'text', 0);
        $alist = ["0 - Todos os campos possíveis e mais um pouco", "1 - Campos básicos", "2 - Campos básicos oper acima 5k", "3 - Agrupado por CNPJ", "4 - Agrupado por Mês"];
        foreach($alist as $choice) {     // Stuff the choices in the model
            $model5->append(array($choice));
        }
        $combobox5->set_active(1);


        $lbl_6 	= new GtkLabel("Valor Mínimo:");
        $combobox6 = new GtkComboBox();  // Create a combobox
        if (defined("GObject::TYPE_STRING")) {  // Create a model
            $model6 = new GtkListStore(GObject::TYPE_STRING);
        } else {
            $model6 = new GtkListStore(Gtk::TYPE_STRING);
        }
        $combobox6->set_model($model6);   // Set up the combobox
        $cellrenderer6 = new GtkCellRendererText();
        $combobox6->pack_start($cellrenderer6);
        $combobox6->set_attributes($cellrenderer6, 'text', 0);
        $alist = ['Exclui Cancelados/Inutilizados', '0', '0,01', '1000', '10000', '100000'];
        foreach($alist as $choice) {     // Stuff the choices in the model
            $model6->append(array($choice));
        }
        $combobox6->set_active(1);

        $dialog->vbox->pack_start($lbl_1, false, false, 3);
        $dialog->vbox->pack_start($combobox, false, false, 3);
        if ($showMaxCells) {
            $dialog->vbox->pack_start($lbl_2, false, false, 3);
            $dialog->vbox->pack_start($combobox2, false, false, 3);
        }
        if ($showSetToDataType) {
            $dialog->vbox->pack_start($lbl_3, false, false, 3);
            $dialog->vbox->pack_start($combobox3, false, false, 3);
        }
        if ($showNivelDetalhe) {
            $dialog->vbox->pack_start($lbl_5, false, false, 3);
            $dialog->vbox->pack_start($combobox5, false, false, 3);
        }
        if ($showValMin) {
            $dialog->vbox->pack_start($lbl_6, false, false, 3);
            $dialog->vbox->pack_start($combobox6, false, false, 3);
        }
        
        if (!is_null($opt4lbl)) {
            $lbl_4 	= new GtkLabel($opt4lbl);
            $dialog->vbox->pack_start($lbl_4, false, false, 3);
            if (!is_array($opt4field)) {
                if ($opt4field == 'GtkEntry') {
                    $entry4 = new GtkEntry('');
                    $dialog->vbox->pack_start($entry4, false, false, 3);
                } else {
                    if ($opt4field == 'GtkTextView') {
                        $textBuffer4 = new GtkTextBuffer();
                        $scrolledwindow4 = new GtkScrolledWindow();
                        $view4 = new GtkTextView();
                        $view4->set_wrap_mode(Gtk::WRAP_WORD_CHAR);
                        $scrolledwindow4->viewer = $view4;
                        $scrolledwindow4->set_policy(Gtk::POLICY_NEVER,Gtk::POLICY_ALWAYS); 
                        $textBuffer4->set_text('');
                        $scrolledwindow4->viewer->set_buffer($textBuffer4);
                        $scrolledwindow4->add($scrolledwindow4->viewer); 
                        $dialog->vbox->pack_start($scrolledwindow4);
                    } else {
                        h_wecho("Erro.... Por enquanto, opt4field deve ser somente array com lista de valores (combobox) ou 'GtkEntry' ou 'GtkTextView'.\n");
                        $dialog->destroy();
                        return false;
                    }
                }
            } else {
                $lbl_4 	= new GtkLabel($opt4lbl);
                $combobox4 = new GtkComboBox();  // Create a combobox
                if (defined("GObject::TYPE_STRING")) {  // Create a model
                    $model4 = new GtkListStore(GObject::TYPE_STRING);
                } else {
                    $model4 = new GtkListStore(Gtk::TYPE_STRING);
                }
                $combobox4->set_model($model4);   // Set up the combobox
                $cellrenderer4 = new GtkCellRendererText();
                $combobox4->pack_start($cellrenderer4);
                $combobox4->set_attributes($cellrenderer4, 'text', 0);
                $alist = $opt4field;
                foreach($alist as $choice) {     // Stuff the choices in the model
                    $model4->append(array($choice));
                }
                $combobox4->set_active(0);
            
                $dialog->vbox->pack_start($combobox4, false, false, 3);
                
            }
        }

        $dialog->add_button(Gtk::STOCK_CANCEL, Gtk::RESPONSE_CANCEL);
        $dialog->add_button(Gtk::STOCK_OK, Gtk::RESPONSE_OK);

        $dialog->show_all();
        $response_id = $dialog->run();

        if ($response_id != Gtk::RESPONSE_OK) {
            h_wecho("Finalizando... Usuário cancelou a operação.\n");
            $dialog->destroy();
            return false;
        }

        $model = $combobox->get_model();
        $selection = $model->get_value($combobox->get_active_iter(), 0);
        $this->osf = mb_substr($selection, 0, 11);
        $model2 = $combobox2->get_model();
        $selection2 = $model2->get_value($combobox2->get_active_iter(), 0);
        $this->maxCells = $selection2;
        $model3 = $combobox3->get_model();
        $selection3 = $model3->get_value($combobox3->get_active_iter(), 0);
        $this->setToDataType = $selection3;
        $model5 = $combobox5->get_model();
        $selection5 = $model5->get_value($combobox5->get_active_iter(), 0);
        $this->nivelDetalhe = intval(substr($selection5, 0, 1));
        $model6 = $combobox6->get_model();
        $selection6 = $model6->get_value($combobox6->get_active_iter(), 0);
        if($this->valMin == 'Exclui Cancelados/Inutilizados') $this->valMin = '-1';
        $this->valMin = intval(str_replace(',', '.', $selection6));
        if ($this->maxCells == "Ilimitado (Somente .txt)") {
            if($this->setToDataType == 'txt') $this->maxCells = -1;
            else $this->maxCells = 1000000; // ou seja, se não for txt vai pra máxima possível do html        
        }
        if (!is_null($opt4lbl)) {
            if (!is_array($opt4field)) {
                if ($opt4field == 'GtkEntry') $this->opt4Sel = $entry4->get_text();
                if ($opt4field == 'GtkTextView') $this->opt4Sel = $textBuffer4->get_text($textBuffer4->get_start_iter(), $textBuffer4->get_end_iter());
            } else {
                $model4 = $combobox4->get_model();
                $selection4 = $model4->get_value($combobox4->get_active_iter(), 0);
                $this->opt4Sel = $selection4;
            }
        }
        $dialog->destroy();
        h_wecho("Ok, OSF selecionada: {$this->osf};" . ($showMaxCells ? " Quantidade Máxima de Células: " . ($this->maxCells == -1 ? "ilimitado" : $this->maxCells) . ";" : '') . ($showSetToDataType ? " Exportando para o formato {$this->setToDataType};" : '') . ($showNivelDetalhe ? " Nível de detalhe: {$this->nivelDetalhe};" : '') . ($showValMin ? " Valor Mínimo: {$this->valMin};" : '') . "\n");

        $this->saveLastData();
        
        return true;

    }
 


    public function getDatabasesOsfSqlite($osf) {
        $this->setPrResultCnpjFromOsf($osf);
        // ##TODO##... primeiro tenta organizar tudo, inserir o banco de dados [cv] na lista de Databases, etc...
        // mas se já houve isso anteriormente, não faz
        $filename = "cv_{$this->osf}";
        if (PR::$resultCnpj <> '') $filename = PR::$resultCnpj . "\\" . $filename;
        //h_wecho("{$filename}\n");
        require_once CVI_SRC . '/CvSqlite.php';
        if (!file_exists(CVI_RESULT . "\\" . $filename . ".db3")) {
            // caso não exista db3 cv, cria 
            $cvSqlite = new CvSqlite(null ,null ,$filename);	// Acesso ao CvSqlite
            $sql = <<<EOD
DROP TABLE IF EXISTS cfopd;
CREATE TABLE cfopd (
  cfop int PRIMARY KEY, 
  dfi text, 
  st text, 
  classe text, 
  g1 text, 
  c3 text, 
  g2 text, 
  g3 text, 
  descri_simplif text, 
  descri text, 
  pod_creditar text
);
DROP TABLE IF EXISTS regOrig;
CREATE TABLE regOrig (
  idRegistroDeOrigem int PRIMARY KEY, 
  origem text, 
  tp_origem text
);
DROP TABLE IF EXISTS cfopEntSai;
CREATE TABLE cfopEntSai (
  cfopDfe int PRIMARY KEY, 
  cfopEfd int
);
DROP TABLE IF EXISTS tipoJuridico;
CREATE TABLE tipoJuridico (
  idTipoJuridico int PRIMARY KEY, 
  TipoJuridico text
);
EOD;
            $cvSqlite->exec($sql);
            $cvSqlite->insertIntoTableFromTxt( CVI_TABLES . '/cfopd.txt', 'cfopd');
            $cvSqlite->insertIntoTableFromTxt( CVI_TABLES . '/regOrig.txt', 'regOrig');
            $cvSqlite->insertIntoTableFromTxt( CVI_TABLES . '/cfopEntSai.txt', 'cfopEntSai');
            $cvSqlite->insertIntoTableFromTxt( CVI_TABLES . '/TipoJuridico.txt', 'tipoJuridico');

        } else {
            // caso exista db3 cv, somente abre 
            $cvSqlite = new CvSqlite(null, null, $filename);	// Acesso ao CvSqlite
        }
        $cvSqlite->db3Attach(str_replace('cv_', 'osf', $filename));	// Acesso ao CvSqlite

        @$res = $cvSqlite->query("SELECT max(versao) AS versao FROM _dbo_Versao;");
        if ($res === False) h_wecho("##ERRO##: " . $db->lastErrorMsg() . "\n");
        else {
            $param = $res->fetchArray(SQLITE3_ASSOC);
            Pr::$saficVersao = $param['versao'];
            h_wecho("Versão do DBO Safic salva em Pr::saficVersao: {$param['versao']}\n");
        }                    

        return $cvSqlite;
    }    

    public function getOsfListSqlite($pr) {
        h_wecho("Lista de Auditorias:\n");
        $this->aGetOsfList = array();
        $osfList = array();
        $allFiles = array();
        $pr->cvh->recursiveFilemtime(CVI_RESULT, $allFiles, 'db3');
        foreach($allFiles as $key => $value) {
            if (mb_substr(basename($key), 0, 3) == 'osf' && mb_strlen(basename($key)) == 18) { 
                $osf = mb_substr( mb_substr(basename($key), 0, -4), 3);
                //h_log("OSF: {$osf}\n");
                if ($db = new \SQLite3($key)) {
                    @$res = $db->query("SELECT razao, cnpj, ie FROM _dbo_auditoria WHERE numOsf = '{$osf}';");
                    if ($res === False) h_wecho("##ERRO## NA OSF {$osf}, arquivo db3 {$key}: " . $db->lastErrorMsg() . "\n");
                    else {
                        $param = $res->fetchArray(SQLITE3_ASSOC);
                        h_wecho("CNPJ: {$param['cnpj']} OSF: {$osf} IE: {$param['ie']}  {$param['razao']}\n");                       
                        $osfListData = $osf . " - " . mb_substr($param['razao'], 0, 25);
                        $this->aGetOsfList[$osf]['cnpj'] = $param['cnpj'];
                        $this->aGetOsfList[$osf]['ie'] = $param['ie'];
                        $this->aGetOsfList[$osf]['razao'] = $param['razao'];
                    }                    
                } else {
                    h_wecho("OSF: {$osf} -> Não consegui abrir o arquivo {$key}... Erro: " . $db->lastErrorMsg() . "\n");
                }
                $osfList[] = $osfListData;
            }
        }
        return $osfList;
    }

    public function setPrResultCnpjFromOsf($osf) {
        $cnpj = $this->aGetOsfList[$osf]['cnpj'];
        PR::$resultCnpj = $cnpj;
    }



    // Trecho SqlSrv
    public function adoDbOpen($adoDb) {
        $adoDb->info();
        if ($adoDb->state != "Running") {
            h_wecho("\n\nFalha!! SqlLocalDb SaficV150 parado... Movimente o Safic e tente novamente\n\n");
            return false;
        } else {
            h_wecho("SqlLocalDb em funcionamento! State: {$adoDb->state}" . ($adoDb->state == "Running" ? " - Pipe Name: {$adoDb->pipeName}" : "") . "\n");
        }
        $adoDb->open(); 
        $this->getDatabases($adoDb);   // é importante que este esteja bem no início, porque ele garante o attach do db [cv], caso não esteja attachado
        return true;
    }

    public function getDatabases($adoDb) {
        $this->databases = array();
        $rs = $adoDb->db->Execute("SELECT QUOTENAME(name) AS f1 FROM sys.databases ORDER BY name"); 
        while (!$rs->EOF) { 
            $this->databases[] = $rs->Fields['f1']->Value;
            $rs->MoveNext(); 
        }         
    }

    public function getOsfList($adoDb, $pr) {
        $this->aGetOsfList = array();
        
        //$sql = "select [SaficV1_0].[dbo].[Auditoria].* from [SaficV1_0].[dbo].[Auditoria]";
        //$fileName = "Safic-AuditoriasDisponiveis";
        //$queryTitle = "Listagem De Auditorias";    
        //$pr->cvSqlToData->run($adoDb, $sql, $fileName, $queryTitle);

        $sql = "SELECT numOsf, identificadorAuditoria, razao, cnpj, ie FROM [SaficV1_0].[dbo].[Auditoria]";
        $adoDb->execute($sql);
        h_wecho("Lista de Auditorias:\n");
        $osfList = array();
        while (!$adoDb->rs->EOF) {
            $adoDb->getLine(true);  // quando coloca True, vem em UTF8
            $osfList[] = $adoDb->rsData[0] . " - " . $adoDb->rsData[3] . " - " . mb_substr($adoDb->rsData[2], 0, 25);
            h_wecho("OSF: {$adoDb->rsData[0]}  Identificador:{$adoDb->rsData[1]}  Contribuinte: CNPJ {$adoDb->rsData[3]} - {$adoDb->rsData[2]}\n");
            $this->aGetOsfList[$adoDb->rsData[0]]['cnpj'] = $adoDb->rsData[3];
            $this->aGetOsfList[$adoDb->rsData[0]]['ie'] = $adoDb->rsData[4];
            $this->aGetOsfList[$adoDb->rsData[0]]['razao'] = $adoDb->rsData[2];
            $adoDb->rs->MoveNext(); 
        }
        return $osfList;
    }
      
    public function getDatabasesOsf($adoDb, $osf) {
        // funciona assim... primeiro tenta organizar tudo, inserir o banco de dados [cv] na lista de Databases, etc...
        // mas se já houve isso anteriormente e o [cv] está na osf errada, é necessário desatachar e tentar de novo
        // por isso que é possível que haja necessidade de se fazer duas vezes
        $retStatus = $this->getDatabasesOsfAux($adoDb, $osf);
        if ($retStatus == 'DesatacharCv') {
            h_wecho("...Não corresponde... então refazendo, porque [cv] da lista de Databases é de outra OSF. Há necessidade de desatachar e atachar o .mdf correto.\nFazendo isso agora! Reabrindo os bancos de dados!\n");
            $adoDb->db->Execute("EXEC sp_detach_db [cv]");
            // não se pode esquecer de remover do array $this->databases... depois, $this->getDatabasesOsfAux vai inserir novamente
                //h_wecho(print_r($this->databases, true));
                //h_wecho("[cv]\n");            
            unset($this->databases[ array_search('[cv]', $this->databases) ]);
            // refazendo, com [cv] desatachado
            $retStatus = $this->getDatabasesOsfAux($adoDb, $osf);
            if ($retStatus == 'DesatacharCv') h_werro_die("#ERRO#  em CvSaficLib::getDatabasesOsf() Não consegui destachar o [cv]!!!");
        }
        $this->setPrResultCnpjFromOsf($osf);
        return $retStatus;
    } 

    protected function getDatabasesOsfAux($adoDb, $osf) {
        $sql = "SELECT QUOTENAME(name) FROM sys.databases WHERE name LIKE '%{$osf}%' ORDER BY name";
        $adoDb->execute($sql);
        h_wecho("Lista de Banco de Dados da OSF:\n");
        $this->sfdb = array();
        $dblistok = false;
        if(!$adoDb->rs->EOF) { $adoDb->getLine(); $this->sfdb[] = $adoDb->rsData[0]; $adoDb->rs->MoveNext(); } 
        if(!$adoDb->rs->EOF) { $adoDb->getLine(); $this->sfdb[] = $adoDb->rsData[0]; $adoDb->rs->MoveNext(); }
        if(!$adoDb->rs->EOF) { $adoDb->getLine(); $this->sfdb[] = $adoDb->rsData[0]; $adoDb->rs->MoveNext(); }
        if(!$adoDb->rs->EOF) { $adoDb->getLine(); $this->sfdb[] = $adoDb->rsData[0]; $adoDb->rs->MoveNext(); }
        if(!$adoDb->rs->EOF) { $adoDb->getLine(); $this->sfdb[] = $adoDb->rsData[0]; $adoDb->rs->MoveNext(); }
        if(!$adoDb->rs->EOF) { $adoDb->getLine(); $this->sfdb[] = $adoDb->rsData[0]; $adoDb->rs->MoveNext(); }
        if(!$adoDb->rs->EOF) { $adoDb->getLine(); $this->sfdb[] = $adoDb->rsData[0]; $adoDb->rs->MoveNext(); }
        if(!$adoDb->rs->EOF) { $adoDb->getLine(); $this->sfdb[] = $adoDb->rsData[0]; $dblistok = true; }
        if (!$dblistok) {
            h_werro_die("Finalizando... Não consegui localizar todos os bancos de dados necessários para a OSF {$osf}.\n\nPossível razão: Verifique se o Safic está aberto, logado e 'vivo'\n");
            //return false;
        }
        h_wecho("Banco de Dados Principal:{$this->sfdb[0]}\n");
        h_wecho("Banco de Dados Dfe 1:{$this->sfdb[1]}\n");
        h_wecho("Banco de Dados Dfe 2:{$this->sfdb[2]}\n");
        h_wecho("Banco de Dados Dfe 3:{$this->sfdb[3]}\n");
        h_wecho("Banco de Dados DocAtrib 1:{$this->sfdb[4]}\n");
        h_wecho("Banco de Dados DocAtrib 2:{$this->sfdb[5]}\n");
        h_wecho("Banco de Dados DocAtrib 3:{$this->sfdb[6]}\n");
        h_wecho("Banco de Dados Aux:{$this->sfdb[7]}\n");

        $appDataSaficOsfDir = $_SERVER["LOCALAPPDATA"] . "\\Safic\\" . str_replace('[', '', str_replace(']', '', $this->sfdb[0]));
        if (! is_dir($appDataSaficOsfDir)) $appDataSaficOsfDir = str_ireplace('C:', 'F:', $appDataSaficOsfDir);
        if (! is_dir($appDataSaficOsfDir)) $appDataSaficOsfDir = str_ireplace('F:', 'G:', $appDataSaficOsfDir);
        if (! is_dir($appDataSaficOsfDir)) $appDataSaficOsfDir = str_ireplace('G:', 'H:', $appDataSaficOsfDir);
        if (! is_dir($appDataSaficOsfDir)) $appDataSaficOsfDir = str_ireplace('H:', 'I:', $appDataSaficOsfDir);
        if (! is_dir($appDataSaficOsfDir)) $appDataSaficOsfDir = str_ireplace('I:', 'J:', $appDataSaficOsfDir);
        if (! is_dir($appDataSaficOsfDir)) 
            h_werro_die("#ERRO# Não consegui localizar o diretório {$appDataSaficOsfDir}. Procurei em C:, F:, G:, H:, I: e J: ... Será que está em outro drive?");
        h_wecho("Conferindo agora se há o banco de dados [cv] físico em {$appDataSaficOsfDir}:\n");
        if (file_exists($appDataSaficOsfDir . "\\cv.mdf") && file_exists($appDataSaficOsfDir  . "\\cv.ldf")) {
            h_wecho("--> Localizado ambos! São eles:\n  `---->{$appDataSaficOsfDir}\\cv.mdf\n  `---->{$appDataSaficOsfDir}\\cv.ldf\n");
        } else {
            if (!file_exists($appDataSaficOsfDir . "\\cv.mdf")) {
                if (!copy(str_replace("/", "\\", CVI_TABLES) . "\\cv.mdf", $appDataSaficOsfDir . "\\cv.mdf"))
                    h_werro_die("#ERRO# Não consegui copiar " . str_replace("/", "\\", CVI_TABLES) . "\\cv.mdf para" . $appDataSaficOsfDir . "\\cv.mdf");
            }
            if (!file_exists($appDataSaficOsfDir . "\\cv.ldf")) {
                if (!copy(str_replace("/", "\\", CVI_TABLES) . "\\cv.ldf", $appDataSaficOsfDir . "\\cv.ldf"))
                    h_werro_die("#ERRO# Não consegui copiar " . str_replace("/", "\\", CVI_TABLES) . "\\cv.ldf para" . $appDataSaficOsfDir . "\\cv.ldf");
            }
            if (file_exists($appDataSaficOsfDir . "\\cv.mdf") && file_exists($appDataSaficOsfDir  . "\\cv.ldf")) {
                h_wecho("Ok, copiado para {$appDataSaficOsfDir}\\cv.mdf e também {$appDataSaficOsfDir}\\cv.ldf !");
            } else {
                h_werro_die("#ERRO# Tentei copiar, mas  não foi copiado {$appDataSaficOsfDir}\\cv.mdf e também {$appDataSaficOsfDir}\\cv.ldf !");                
            }
        }
        if (array_search('[cv]', $this->databases) !== false) {
            h_wecho("Banco de Dados [cv] já está aberto. Conferindo agora se corresponde fisicamente ao da OSF selecionada...\n");
            $sql = <<<EOD
SELECT d.name DatabaseName, f.physical_name AS PhysicalName, f.type_desc TypeofFile
FROM sys.master_files f
INNER JOIN sys.databases d ON d.database_id = f.database_id
WHERE d.name = 'cv'
EOD;
            $adoDb->execute($sql);
            if (!$adoDb->rs->EOF) {
                $adoDb->getLine();
                if (dirname($adoDb->rsData[1]) == $appDataSaficOsfDir) h_wecho("--> Ok! [cv] é o .mdf que está na pasta " . dirname($adoDb->rsData[1]) . "\n");
                else return 'DesatacharCv'; // vai ter que desatachar [cv] e refazer este método getDatabasesOsfAux
            } else {
                h_werro_die("#ERRO# em CvSaficLib::getDatabasesOsf()... O select não retornou onde está [cv] fisicamente...");
            }
            
        } else {
            h_wecho("Banco de Dados [cv] não estava na lista de databases. 'Atachando' então o arquivo correto, correspondente à OSF selecionada!\n");
            $cvDir =  str_replace("/", "\\", $appDataSaficOsfDir);
            $sql = <<<EOD
CREATE DATABASE [cv] ON 
( FILENAME = '{$cvDir}\cv.mdf' ),
( FILENAME = '{$cvDir}\cv.ldf' )
FOR ATTACH
EOD;
            $adoDb->db->Execute($sql);
            $this->databases[] = '[cv]';
            h_wecho("Ok! Arquivo .mdf de [cv] da pasta {$cvDir} 'atachado' com sucesso!\n");
        } 

        return $this->sfdb;
    }

}

