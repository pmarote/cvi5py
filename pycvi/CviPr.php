<?php

require_once CVI_SRC . '/safic/CvSaficLib.php';
require_once CVI_SRC . '/safic/CvAdoDb.php';
require_once CVI_SRC . '/CvSqlToData.php';
require_once CVI_SRC . '/CviDialogs.php';
require_once CVI_SRC . '/CvHelpers.php';

class Pr {

    public $db;                     // objeto para Sqlite3
    public $cvSaficLib;             // objeto para CvSaficLib
    public $adoDb;	                // objeto para AdoDb
    public $cvSqlToData;            // objeto CvSqlToData
    public $cviDialogs;             // objeto CviDialogs
    public $cvh;                    // objeto CvHelpers
    
    public $aud_params = array();   // array de objetos PrMenu
    
    public static $resultCnpj;      // CNPJ da empresa em uso, onde será exportado para CVI_RESULT
                                    // é estático para poder ser acessado diretamente de classes "filhas"
                                    // inicialmente começa com '', ou seja, coloca diretamente em CVI_RESULT e não na subpasta com CNPJ
                                    // veja que esta variável é string, e o cnpj deve ter 14 dígitos, zeros a esquerda, sem traços, barras ou pontos
                                    
    public static $saficVersao;     // importante porque as bases de dados do Safic estão mudando. Então alguns SQLs se atualizam dependendo da versao. 
                                    
//    public static $ppr;             // ver explicação em __construct()

    public $options = array();		// array de opções


    public function __construct()
    {
//        self::$ppr = $this;         // comando estranho, mas possibilita eu conseguir qualquer acesso à
//                                    // qualquer método PR como estático (ou propriedade estática), em qualquer lugar....
//                                    // está como PPR, ao invés de PR, porque estou ainda regularizando os nomes, e pegando esse conceito do projeto PPR
        $this->cvSaficLib = new CvSaficLib;	
        $this->adoDb = new AdoDb;	// Acesso ao SqlLocalDb
        $this->cvSqlToData = new CvSqlToData;
        $this->cviDialogs = new CviDialogs;
        $this->cvh = new \PMarote\PPR\CvHelpers();
        self::$resultCnpj = '';
        self::$saficVersao = '';

        // Opções: Ver projeto cv3, tá bem explicado lá
        // ['label'] é o texto que vai aparecer quando o usuário clicar em opções
        // ['tipo'] pode ser 'CheckButton' (True ou False), 'Entry' (campo texto), 'EntryInt' (campo inteiro) ou 'ComboBox' (ComboBox drop down list)
        // se ['tipo'] = 'ComboBox', deverá haver um array com a listagem em ['alist'], contendo em cada linha, valor e descrição
        $this->options['excelSave'] = True;		// logical Após abrir o arquivo .txt no Excel, salver ?  
        $this->options['label']['excelSave'] = 'Após abrir o arquivo .txt no Excel, salva';
        $this->options['tipo']['excelSave'] = 'CheckButton';
        // exemplo de EntryInt
        //$this->options['limit_sql'] = 300000;	// Limite máximo das Querys, definido em opções, usado em abre_excel, na exportação .txt
        //$this->options['label']['limit_sql'] = 'Limite de linhas nas consultas : ';
        //$this->options['tipo']['limit_sql'] = 'EntryInt';
        // exemplo e ComboBox
        //$this->options['nivdetmes'] = 4;	// Nível de detalhe padrão quando da visualização de dados dentro do ano
        //$this->options['label']['nivdetmes'] = 'Nível de detalhe padrão quando da visualização de dados dentro do ano : ';
        //$this->options['tipo']['nivdetmes'] = 'ComboBox';
        //$this->options['alist']['nivdetmes'] = array(
            //1 => 'Mensal',
            //2 => 'Bimestral',
            //3 => 'Trimestral',
            //4 => 'Quadrimestral',
            //6 => 'Semestral'
        //);
        $this->readOptions();

    }

    // ** Seção Options
    public function saveOptions() {
        // Salva somente as opções que devem ser carregadas em logins futuros
        // Ou seja, tudo o que não é array, mais precisamente, excluindo ['label'], ['tipo'] e ['alist']
        $arqData =  CVI_LOG . "/Cvi5.dat";
        $asave = array();
        foreach ($this->options as $indice => $valor) {
            if (! is_array($this->options[$indice])) $asave[$indice] = $valor;
        }
        if(!file_put_contents($arqData, serialize($asave))) 
            h_werro_die("Pr::saveOptions() ##FATAL ERROR... Could not save {$arqData}\n");
    }

    public function readOptions() {
        $arqData =  CVI_LOG . "/Cvi5.dat";
        if (!file_exists($arqData)) return false;
        if (! $optData = file_get_contents($arqData))
            h_werro_die("Pr::readOptions() ##FATAL ERROR... {$arqData} not readable\n");
        $aread = unserialize($optData);
        //debug_log(print_r($aread, True));
        foreach ($aread as $indice => $valor) $this->options[$indice] = $valor;
    }



    public function aud_registra(PrMenu $aud_param) {
        // aud_registra - Registra a auditoria PrMenu
        $this->aud_params[] = $aud_param;
    }
  
    public function aud_executa(PrMenu $aud_param) {
        // aud_executa - Chamado a partir do click no menu, em leitura.php, em function on_menu_select($menu_item)
        // $aud_param é o objeto PrMenu contendo os parâmetros daquela opção
        //if ($this->aud_disponivel($aud_param->use)) {
            // Abre os arquivos conforme $aud_param['use'];
            // $this->aud_abre_db_e_attach($aud_param->use);
            $callback = $aud_param->callback;
            $callback();
        //} else wecho("\nErro: Auditoria '{$aud_param->menu} - {$aud_param->submenu}' não disponível - Falta banco de dados\n");
    }

}

class PrMenu {
  // Registra uma opção no menu auditoria
  // $callback -> nome da função a ser chamada no caso de escolha do item no menu
  // $menu -> nome do item no menu
  // $submenu -> nome do item no submenu
  // $use (opcional)-> bancos de dados necessários	Exemplo: "p32, nfe, gia" -> Abre p32 e attach nfe e gia
  public $callback, $menu, $submenu, $use;

  function __construct( $callback, $menu, $submenu, $use = '') {
	$this->callback = $callback;
	$this->menu 	= $menu;
	// o submenu é "aperfeiçoado" automaticamente com os bancos de dados que ele usa, entre colchetes
	$this->submenu =  ( $use == '' ? '' : '[' . str_replace(',', '][', $use) . '] ' ) . $submenu;
	$this->use		= $use;
  }
}


