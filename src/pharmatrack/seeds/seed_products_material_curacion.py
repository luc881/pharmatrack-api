"""
pharmatrack/seeds/seed_products_material_curacion.py
"""
from sqlalchemy.orm import Session
from pharmatrack.db.session import SessionLocal
from pharmatrack.seeds.helpers.seeder_helpers import (
    get_or_create_brand,
    get_or_create_category,
    get_or_create_product,
)

ROOT = "Material de curación"

MATERIAL_CURACION = [
    {"sku": "010", "title": "Gotero vidrio", "brand": "Genérico", "cost": 5},
    {"sku": "0100707387509484", "title": "Tegaderm film chico", "brand": "3M", "cost": 25},
    {"sku": "0100707387509507", "title": "Tegaderm film grande", "brand": "3M", "cost": 30},
    {"sku": "011", "title": "Gotero plastico", "brand": "Genérico", "cost": 5},
    {"sku": "0470", "title": "Sutura 4/0", "brand": "Genérico", "cost": 70},
    {"sku": "05", "title": "Glucosa", "brand": "Genérico", "cost": 40},
    {"sku": "06", "title": "Sutura", "brand": "Genérico", "cost": 100},
    {"sku": "073796714222", "title": "Monitor de presion Ombron", "brand": "Ombron", "cost": 950},
    {"sku": "2692", "title": "Nylon 2/0", "brand": "Genérico", "cost": 70},
    {"sku": "382903249138", "title": "Jeringa para insulina 0.3ml", "brand": "Genérico", "cost": 65},
    {"sku": "382903249145", "title": "Jeringa para insulina 0.5ml", "brand": "Genérico", "cost": 65},
    {"sku": "382903249152", "title": "Jeringa para insulina 6mm", "brand": "Genérico", "cost": 65},
    {"sku": "382903267804", "title": "Jeringa para insulina 1ml", "brand": "Genérico", "cost": 65},
    {"sku": "382903882090", "title": "Cateter #18", "brand": "Genérico", "cost": 23},
    {"sku": "4005800024108", "title": "Parche Gallo suelto", "brand": "Genérico", "cost": 8},
    {"sku": "4015630064076", "title": "Accu-Chek Active", "brand": "Accu-Chek", "cost": 280},
    {"sku": "4015630067084", "title": "Accu-Chek Instant", "brand": "Accu-Chek", "cost": 345},
    {"sku": "4015630082988", "title": "Accu-Chek Active aparato", "brand": "Accu-Chek", "cost": 650},
    {"sku": "4015630981977", "title": "Accu-Chek Performance", "brand": "Accu-Chek", "cost": 385},
    {"sku": "4175", "title": "Nylon 3/0", "brand": "Genérico", "cost": 70},
    {"sku": "5044", "title": "Curitas niño", "brand": "Genérico", "cost": 4},
    {"sku": "614143495489", "title": "Nebulizador compresor de aire", "brand": "Genérico", "cost": 950},
    {"sku": "643131501956", "title": "Jeringa 3ml verde", "brand": "Genérico", "cost": 5},
    {"sku": "6594", "title": "Curitas sueltos", "brand": "Genérico", "cost": 2},
    {"sku": "6818", "title": "Acetona 1L", "brand": "Genérico", "cost": 110},
    {"sku": "7500326424243", "title": "Cinta kinesiologica precortada azul", "brand": "Genérico", "cost": 75},
    {"sku": "7500326424250", "title": "Cinta kinesiologica precortada rosa", "brand": "Genérico", "cost": 75},
    {"sku": "7500399003239", "title": "Termometro digital Chech Atek", "brand": "Chech Atek", "cost": 85},
    {"sku": "7501023108818", "title": "Cinta Nexcare grande", "brand": "Nexcare", "cost": 55},
    {"sku": "7501048612109", "title": "Gasa seca esteril aposito", "brand": "Genérico", "cost": 20},
    {"sku": "7501048640751", "title": "Venda enyesada 5cm", "brand": "Genérico", "cost": 28},
    {"sku": "7501048640775", "title": "Venda enyesada 10cm", "brand": "Genérico", "cost": 40},
    {"sku": "7501048640799", "title": "Venda enyesada 15cm", "brand": "Genérico", "cost": 48},
    {"sku": "7501048640829", "title": "Venda enyesada 20cm", "brand": "Genérico", "cost": 75},
    {"sku": "7501048660490", "title": "Jeringa verde 3ml", "brand": "Genérico", "cost": 5},
    {"sku": "7501048660551", "title": "Jeringa 5ml verde", "brand": "Genérico", "cost": 6},
    {"sku": "7501048660582", "title": "Jeringa negra 5ml Protect", "brand": "Protect", "cost": 6},
    {"sku": "7501048660964", "title": "Jeringa ped", "brand": "Genérico", "cost": 5},
    {"sku": "7501048670802", "title": "Termometo Protec", "brand": "Protec", "cost": 85},
    {"sku": "7501048690800", "title": "Venda elastica de alta compresion 5cm", "brand": "Genérico", "cost": 25},
    {"sku": "7501048690879", "title": "Venda elastica de alta compresion 10cm", "brand": "Genérico", "cost": 55},
    {"sku": "7501048692088", "title": "Malla elastica #1", "brand": "Genérico", "cost": 22},
    {"sku": "7501048692187", "title": "Malla elastica #2", "brand": "Genérico", "cost": 25},
    {"sku": "7501048692286", "title": "Malla elastica #3", "brand": "Genérico", "cost": 30},
    {"sku": "7501048692385", "title": "Malla elastica #4", "brand": "Genérico", "cost": 35},
    {"sku": "7501048692484", "title": "Malla elastica #5", "brand": "Genérico", "cost": 38},
    {"sku": "7501048692583", "title": "Malla elastica #6", "brand": "Genérico", "cost": 45},
    {"sku": "7501048693900", "title": "Venda elastica 15cm", "brand": "Genérico", "cost": 35},
    {"sku": "7501048920150", "title": "Guante chico", "brand": "Genérico", "cost": 5},
    {"sku": "7501054502111", "title": "Jeringa 10 ml", "brand": "Genérico", "cost": 10},
    {"sku": "7501073025394", "title": "Jeringa 3ml verde", "brand": "Genérico", "cost": 5},
    {"sku": "7501073025417", "title": "Jeringa 3ml negra", "brand": "Genérico", "cost": 5},
    {"sku": "7501073025431", "title": "Jeringa ped caja", "brand": "Genérico", "cost": 30},
    {"sku": "7501073025523", "title": "Jeringa 5ml negra", "brand": "Genérico", "cost": 6},
    {"sku": "7501073025585", "title": "Jeringa 10ml", "brand": "Genérico", "cost": 10},
    {"sku": "7501125125362", "title": "Equipo de venoclisis", "brand": "Genérico", "cost": 30},
    {"sku": "7501232060631", "title": "Bolsa para urocultivo niño", "brand": "Genérico", "cost": 12},
    {"sku": "7501232060648", "title": "Bolsa para urocultivo niña", "brand": "Genérico", "cost": 12},
    {"sku": "7501463321006", "title": "Pezonera", "brand": "Genérico", "cost": 30},
    {"sku": "7501463325028", "title": "Espejo vaginal", "brand": "Genérico", "cost": 45},
    {"sku": "7501563020038", "title": "Cateter #17", "brand": "Genérico", "cost": 23},
    {"sku": "7501563020076", "title": "Cateter #21", "brand": "Genérico", "cost": 23},
    {"sku": "7501563020083", "title": "Cateter #14", "brand": "Genérico", "cost": 23},
    {"sku": "7501563020090", "title": "Cateter #16", "brand": "Genérico", "cost": 23},
    {"sku": "7501563020113", "title": "Cateter #20", "brand": "Genérico", "cost": 23},
    {"sku": "7501563020366", "title": "Cateter #23", "brand": "Genérico", "cost": 23},
    {"sku": "7501563024593", "title": "Cateter #19", "brand": "Genérico", "cost": 23},
    {"sku": "7501563666601", "title": "Catater #20", "brand": "Genérico", "cost": 23},
    {"sku": "7501563666861", "title": "Cateter #22", "brand": "Genérico", "cost": 23},
    {"sku": "7501565606056", "title": "Algodon 300g", "brand": "Genérico", "cost": 95},
    {"sku": "7501565606117", "title": "Algodon 25g", "brand": "Genérico", "cost": 15},
    {"sku": "7501626700778", "title": "Antibenzil jabon quirurgico", "brand": "Antibenzil", "cost": 55},
    {"sku": "7501634612025", "title": "Rulav ch", "brand": "Rulav", "cost": 65},
    {"sku": "7501634612032", "title": "Rulav mediano", "brand": "Rulav", "cost": 65},
    {"sku": "7501634612049", "title": "Rulav grande", "brand": "Rulav", "cost": 65},
    {"sku": "7501868900011", "title": "Gasa 7.5x7.5 suelta", "brand": "Genérico", "cost": 1},
    {"sku": "7501868900035", "title": "Caja gasa ch c/100pz", "brand": "Genérico", "cost": 135},
    {"sku": "7501868900110", "title": "Gasa 10x10 suelta", "brand": "Genérico", "cost": 2},
    {"sku": "7501868900127", "title": "Dibar gasa caja c/10", "brand": "Dibar", "cost": 20},
    {"sku": "7501868900134", "title": "Caja de gasas c/100", "brand": "Genérico", "cost": 160},
    {"sku": "7501868900172", "title": "Caja de gasas c/100", "brand": "Genérico", "cost": 160},
    {"sku": "7501868900509", "title": "Tela adhesiva chica #1", "brand": "Genérico", "cost": 10},
    {"sku": "7501868900523", "title": "Tela adhesiva mediana #2", "brand": "Genérico", "cost": 15},
    {"sku": "7501868900547", "title": "Tela adhesiva grande #3", "brand": "Genérico", "cost": 25},
    {"sku": "7501868900561", "title": "Tela adhesiva xgrande #4", "brand": "Genérico", "cost": 40},
    {"sku": "7501868901100", "title": "Alcohol 125ml", "brand": "Genérico", "cost": 15},
    {"sku": "7501868901117", "title": "Alcohol 250ml", "brand": "Genérico", "cost": 25},
    {"sku": "7501868901124", "title": "Alcohol 500ml", "brand": "Genérico", "cost": 50},
    {"sku": "7501868901131", "title": "Alcohol 1L", "brand": "Genérico", "cost": 90},
    {"sku": "7501868902008", "title": "Venda elastica 5cm", "brand": "Genérico", "cost": 14},
    {"sku": "7501868902107", "title": "Venda elastica 7.5cm", "brand": "Genérico", "cost": 17},
    {"sku": "7501868902206", "title": "Venda elastica 10cm", "brand": "Genérico", "cost": 24},
    {"sku": "7501868902404", "title": "Venda elastica 20cm", "brand": "Genérico", "cost": 45},
    {"sku": "7501868902602", "title": "Venda elastica 30cm", "brand": "Genérico", "cost": 48},
    {"sku": "7501868910003", "title": "Algodon 100g", "brand": "Genérico", "cost": 33},
    {"sku": "7501868910027", "title": "Algodon Dibar 300g", "brand": "Dibar", "cost": 95},
    {"sku": "7501868910034", "title": "Algodon 50g", "brand": "Genérico", "cost": 18},
    {"sku": "7501868910041", "title": "Algodon 25g", "brand": "Genérico", "cost": 15},
    {"sku": "7501868910058", "title": "Algodon Dibar 10g", "brand": "Dibar", "cost": 6},
    {"sku": "7501868920163", "title": "Gel antiseptico 500ml", "brand": "Genérico", "cost": 60},
    {"sku": "7501868950009", "title": "Tira leche de cristal", "brand": "Genérico", "cost": 55},
    {"sku": "7501877650402", "title": "Lava ojos de vidrio", "brand": "Genérico", "cost": 25},
    {"sku": "7501877651324", "title": "Rodillera elastica ch", "brand": "Genérico", "cost": 85},
    {"sku": "7501877651331", "title": "Rodillera elastica med", "brand": "Genérico", "cost": 85},
    {"sku": "750210680995", "title": "Agua destilada 1L", "brand": "Genérico", "cost": 33},
    {"sku": "7502210680995", "title": "Agua destilada 1L", "brand": "Genérico", "cost": 33},
    {"sku": "7502210682265", "title": "Broche para venda", "brand": "Genérico", "cost": 1},
    {"sku": "7502224240642", "title": "Guante de latex chico", "brand": "Genérico", "cost": 5},
    {"sku": "7502224240659", "title": "Guante mediano", "brand": "Genérico", "cost": 5},
    {"sku": "7502224240666", "title": "Guante grande", "brand": "Genérico", "cost": 5},
    {"sku": "7502224245890", "title": "Cateter #18", "brand": "Genérico", "cost": 23},
    {"sku": "7502224245906", "title": "Cateter #20", "brand": "Genérico", "cost": 23},
    {"sku": "7502224245913", "title": "Cateter #22", "brand": "Genérico", "cost": 23},
    {"sku": "7502224245920", "title": "Cateter #24", "brand": "Genérico", "cost": 23},
    {"sku": "7502241150160", "title": "Vaso humidificador", "brand": "Genérico", "cost": 130},
    {"sku": "7502246642073", "title": "Microdacyn ch", "brand": "Microdacyn", "cost": 185},
    {"sku": "7502280170181", "title": "Bote irrigador completo", "brand": "Genérico", "cost": 85},
    {"sku": "7503006698316", "title": "Microdacyn", "brand": "Microdacyn", "cost": 285},
    {"sku": "7504005010529", "title": "Catater para suministro de oxigeno adulto", "brand": "Genérico", "cost": 35},
    {"sku": "7506022307040", "title": "Mascarilla para oxigeno ped", "brand": "Genérico", "cost": 95},
    {"sku": "7506022308245", "title": "Canula nasal para oxigeno adulto", "brand": "Genérico", "cost": 45},
    {"sku": "7506022308252", "title": "Canula nasal para oxigeno ped", "brand": "Genérico", "cost": 45},
    {"sku": "7506022314550", "title": "Mascarilla con nebulizador adulto", "brand": "Genérico", "cost": 75},
    {"sku": "7506022322395", "title": "Venoclisis", "brand": "Genérico", "cost": 30},
    {"sku": "7506313000353", "title": "Agua destilada 1L", "brand": "Genérico", "cost": 33},
    {"sku": "7506346600131", "title": "Algodon 10g", "brand": "Genérico", "cost": 6},
    {"sku": "7506346600193", "title": "Torundas 150", "brand": "Genérico", "cost": 35},
    {"sku": "7506346604122", "title": "Tobillera mediana", "brand": "Genérico", "cost": 125},
    {"sku": "7506346604139", "title": "Tobillera grande", "brand": "Genérico", "cost": 125},
    {"sku": "7506372603113", "title": "Callarin servical mediano", "brand": "Genérico", "cost": 95},
    {"sku": "7506484500591", "title": "Cinta micropore chica blanca", "brand": "Micropore", "cost": 15},
    {"sku": "7506484500607", "title": "Cinta micropore mediana blanca", "brand": "Micropore", "cost": 30},
    {"sku": "7506484500638", "title": "Cinta micropore chica piel", "brand": "Micropore", "cost": 15},
    {"sku": "7506484500645", "title": "Cinta micropore mediana piel", "brand": "Micropore", "cost": 30},
    {"sku": "7506484500652", "title": "Cinta micropore grande piel", "brand": "Micropore", "cost": 65},
    {"sku": "759684154140", "title": "Gel antiseptico 120ml", "brand": "Genérico", "cost": 30},
    {"sku": "759684154232", "title": "Gel antiseptico 60ml", "brand": "Genérico", "cost": 22},
    {"sku": "7702003476594", "title": "Curitas caja", "brand": "Genérico", "cost": 60},
    {"sku": "7891463003034", "title": "Jeringa 5 ml", "brand": "Genérico", "cost": 6},
    {"sku": "7891463003782", "title": "Jeringa 20ml", "brand": "Genérico", "cost": 20},
    {"sku": "812608030088", "title": "Onertouch Delica Plus lancetas", "brand": "Onertouch", "cost": 135},
    {"sku": "896602001039", "title": "Copro", "brand": "Genérico", "cost": 10},
    {"sku": "ABA", "title": "Abatelenguas suelto", "brand": "Genérico", "cost": 2},
    {"sku": "AP", "title": "Aplicadores", "brand": "Genérico", "cost": 20},
    {"sku": "BAC", "title": "Bolsa de agua caliente", "brand": "Genérico", "cost": 120},
    {"sku": "BI", "title": "Bote irrigador", "brand": "Genérico", "cost": 85},
    {"sku": "BST", "title": "Bisturi", "brand": "Genérico", "cost": 12},
    {"sku": "CA", "title": "Cubrebocas azul plisado", "brand": "Genérico", "cost": 5},
    {"sku": "CF", "title": "Cofia", "brand": "Genérico", "cost": 5},
    {"sku": "CI", "title": "Cubrebocas infantil", "brand": "Genérico", "cost": 5},
    {"sku": "7501023108801", "title": "Cinta Nexcare chica", "brand": "Nexcare", "cost": 25},
    {"sku": "CN", "title": "Cubrebocas negro plisado", "brand": "Genérico", "cost": 5},
    {"sku": "CP", "title": "Copro", "brand": "Genérico", "cost": 10},
    {"sku": "CR", "title": "Cubrebocas rosa", "brand": "Genérico", "cost": 5},
    {"sku": "FD", "title": "Ferula para dedo", "brand": "Genérico", "cost": 85},
    {"sku": "FG", "title": "Frasco gotero", "brand": "Genérico", "cost": 30},
    {"sku": "HT", "title": "Huata", "brand": "Genérico", "cost": 10},
    {"sku": "HTTPñ--WEIXIN.QQ.COM-R-8H2LVyZevTePRCJE90JG", "title": "Oximetro Yobekan", "brand": "Yobekan", "cost": 250},
    {"sku": "INS", "title": "Jeringa de insulina suelta", "brand": "Genérico", "cost": 8},
    {"sku": "KNF", "title": "Kn95 inf", "brand": "Genérico", "cost": 10},
    {"sku": "KNN", "title": "KN95 negro", "brand": "Genérico", "cost": 10},
    {"sku": "LO", "title": "Lava ojos plastico", "brand": "Genérico", "cost": 12},
    {"sku": "PA", "title": "Paquete cubrebocas azul", "brand": "Genérico", "cost": 15},
    {"sku": "PLA0", "title": "Perilla 0", "brand": "Genérico", "cost": 22},
    {"sku": "PLA1", "title": "Perilla 1", "brand": "Genérico", "cost": 25},
    {"sku": "PLA2", "title": "Perilla 2", "brand": "Genérico", "cost": 29},
    {"sku": "PLA3", "title": "Perilla 3", "brand": "Genérico", "cost": 33},
    {"sku": "PLA4", "title": "Perilla 4", "brand": "Genérico", "cost": 35},
    {"sku": "PLA5", "title": "Perilla 5", "brand": "Genérico", "cost": 40},
    {"sku": "PLA6", "title": "Perilla 6", "brand": "Genérico", "cost": 45},
    {"sku": "PN", "title": "Paquete cubrebocas negro", "brand": "Genérico", "cost": 15},
    {"sku": "SUTURA 2-0", "title": "Sutura 2-0", "brand": "Genérico", "cost": 70},
    {"sku": "SUTURA 3/0", "title": "Sutura 3/0", "brand": "Genérico", "cost": 70},
    {"sku": "SUTURA 4/0", "title": "Sutura 4/0", "brand": "Genérico", "cost": 70},
    {"sku": "SUTURA 5/0", "title": "Sutura 5/0", "brand": "Genérico", "cost": 70},
    {"sku": "7713042257747", "title": "Contador de pastillas", "brand": "Genérico", "cost": 30},
    {"sku": "7501048335138", "title": "Agua oxigenada 100ml", "brand": "Genérico", "cost": 15},
    {"sku": "7501048335169", "title": "Agua oxigenada 230ml", "brand": "Genérico", "cost": 18},
    {"sku": "7501048335305", "title": "Agua oxigenada 480ml", "brand": "Genérico", "cost": 28},
    {"sku": "7501125100116", "title": "Cloruro de sodio 250 ml", "brand": "Genérico", "cost": 35},
    {"sku": "7501125100123", "title": "Cloruro de sodio 500ml", "brand": "Genérico", "cost": 50},
    {"sku": "7501125100130", "title": "Cloruro de sodio 1L", "brand": "Genérico", "cost": 95},
    {"sku": "7501125100253", "title": "Solucion Hartman 1000ml", "brand": "Genérico", "cost": 95},
    {"sku": "7501125100901", "title": "Solucion Hartmann", "brand": "Genérico", "cost": 95},
    {"sku": "7501125115479", "title": "Cloruro de sodio 100ml", "brand": "Genérico", "cost": 28},
    {"sku": "7501842800412", "title": "Agua oxigenada 1L", "brand": "Genérico", "cost": 45},
    {"sku": "8801038200019", "title": "Navaja suelta", "brand": "Genérico", "cost": 8},
    {"sku": "8801038200026", "title": "Navaja caja c/10", "brand": "Genérico", "cost": 30},
]


def _classify(title: str) -> str:
    t = title.lower()
    if any(x in t for x in ["jeringa", "aguja", "lanceta"]):
        return "Jeringas y agujas"
    if any(x in t for x in ["cateter", "catater", "sonda", "venoclisis"]):
        return "Catéteres y sondas"
    if any(x in t for x in ["gasa", "venda", "aposito"]):
        return "Gasas y vendas"
    if any(x in t for x in ["cinta", "tegaderm", "parche", "tela adhesiva"]):
        return "Cintas y parches"
    if any(x in t for x in ["algodon", "torunda"]):
        return "Algodón y torundas"
    if any(x in t for x in ["alcohol", "antiseptico", "agua oxigenada", "cloruro", "hartman", "microdacyn", "antibenzil"]):
        return "Antisépticos y soluciones"
    if any(x in t for x in ["oxigeno", "canula", "mascarilla", "nebulizador", "vaso humidificador"]):
        return "Oxígeno y terapia respiratoria"
    if any(x in t for x in ["navaja", "bisturi", "gotero", "contador", "abatelengua", "bisturi", "frasco"]):
        return "Instrumental médico"
    if any(x in t for x in ["monitor", "oximetro", "termometro", "accu-chek"]):
        return "Equipos y dispositivos médicos"
    if any(x in t for x in ["rodillera", "tobillera", "callarin", "ferula", "malla"]):
        return "Ortopedia y soporte"
    if any(x in t for x in ["cubrebocas", "cofia", "guante", "kn95"]):
        return "Desechables hospitalarios"
    return "Otros insumos médicos"


def seed_material_curacion(db: Session):
    created = skipped = 0

    for item in MATERIAL_CURACION:
        subcat = _classify(item["title"])
        category_id = get_or_create_category(db, subcat, ROOT)
        brand_id = get_or_create_brand(db, item["brand"])

        cost = float(item["cost"])
        _, was_created = get_or_create_product(
            db,
            title=item["title"],
            sku=item["sku"],
            brand_id=brand_id,
            category_id=category_id,
            price_cost=cost,
            price_retail=round(cost * 1.40, 2),
            description="Material de curación precargado",
        )

        if was_created:
            created += 1
        else:
            skipped += 1

    db.commit()
    print(f"✅ Material de curación insertado: {created}")
    print(f"⚠️  Duplicados omitidos:            {skipped}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_material_curacion(db)
    finally:
        db.close()