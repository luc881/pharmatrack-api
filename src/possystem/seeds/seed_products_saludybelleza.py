from sqlalchemy.orm import Session
from possystem.db.session import SessionLocal
from possystem.models.products.orm import Product
from possystem.models.product_brand.orm import ProductBrand
from possystem.models.product_categories.orm import ProductCategory

# ---------------------------
# Datos crudos (subset ejemplo, puedes expandir igual)
# ---------------------------

SALUD_BELLEZA = [
    {"sku": "020", "title": "Corta uñas mediano", "brand": "Genérico", "cost": 20},
    {"sku": "020800600347", "title": "Tampax Naranja", "brand": "Tampax", "cost": 60},
    {"sku": "025", "title": "Corta uñas para niño", "brand": "Genérico", "cost": 25},
    {"sku": "037836041259", "title": "Hinds Rosas 90ml", "brand": "Hinds", "cost": 24},
    {"sku": "037836041297", "title": "Hinds Tapa Morada 90ml", "brand": "Hinds", "cost": 24},
    {"sku": "037836041303", "title": "Hinds Tapa Morada 230ml", "brand": "Hinds", "cost": 45},
    {"sku": "037836041341", "title": "Hinds Sabila 90ml", "brand": "Hinds", "cost": 24},
    {"sku": "037836041358", "title": "Hinds Sabila 230ml", "brand": "Hinds", "cost": 45},
    {"sku": "037836041389", "title": "Hinds Almedra 90ml", "brand": "Hinds", "cost": 24},
    {"sku": "037836060199", "title": "Ricitos de Oro Accesorios", "brand": "Ricitos de Oro", "cost": 85},
    {"sku": "040", "title": "Corta uñas grande", "brand": "Genérico", "cost": 40},
    {"sku": "045", "title": "Corta uñas grande metalico", "brand": "Genérico", "cost": 45},
    {"sku": "067238891190", "title": "Jabon Dove", "brand": "Dove", "cost": 45},
    {"sku": "070942125352", "title": "Gum para ortodoncial pack", "brand": "Gum", "cost": 175},
    {"sku": "070942302289", "title": "Gum gingivitis", "brand": "Gum", "cost": 155},
    {"sku": "070942302326", "title": "Pasta Gum Paroex", "brand": "Gum", "cost": 65},
    {"sku": "070942307109", "title": "Gum hilo dental con mango", "brand": "Gum", "cost": 40},
    {"sku": "070942507240", "title": "Gum Orthodontic", "brand": "Gum", "cost": 95},
    {"sku": "070942901536", "title": "Kit viajero Gum", "brand": "Gum", "cost": 95},
    {"sku": "1020", "title": "Alicatas", "brand": "Genérico", "cost": 110},
    {"sku": "3014260019723", "title": "Cepillo Oral B Kids", "brand": "Oral B", "cost": 45},
    {"sku": "310119034347", "title": "Renu Fresh", "brand": "Renu", "cost": 110},
    {"sku": "312547321808", "title": "Listerine Cool Mint", "brand": "Listerine", "cost": 75},
    {"sku": "3310000150924", "title": "Aceite de Lavanda", "brand": "Genérico", "cost": 16},
    {"sku": "3311000001391", "title": "Aceite de Aguacate", "brand": "Genérico", "cost": 16},
    {"sku": "3311000001414", "title": "Aceite de Arrayan", "brand": "Genérico", "cost": 16},
    {"sku": "3311000001773", "title": "Agua de Rosas", "brand": "Genérico", "cost": 25},
    {"sku": "4005808630660", "title": "Nivea Aerosol Morado", "brand": "Nivea", "cost": 75},
    {"sku": "4005808829675", "title": "Nivea Classic Touch Rosa Spray", "brand": "Nivea", "cost": 75},
    {"sku": "4005900036711", "title": "Nivea Men Aerosol Black and White", "brand": "Nivea", "cost": 75},
    {"sku": "4005900314758", "title": "Labello Mora", "brand": "Labello", "cost": 85},
    {"sku": "4005900376459", "title": "Nivea Men Invisible Black & White 150 ml Aerosol", "brand": "Nivea", "cost": 75},
    {"sku": "4005900618986", "title": "Nivea Aerosol Black and White", "brand": "Nivea", "cost": 75},
    {"sku": "4005900875013", "title": "Nivea Men Aerosol Deep", "brand": "Nivea", "cost": 75},
    {"sku": "5000174003963", "title": "Fixodent Fresh", "brand": "Fixodent", "cost": 95},
    {"sku": "5000174305449", "title": "Fixodent Original", "brand": "Fixodent", "cost": 95},
    {"sku": "603553651257", "title": "Esponja Corporal Larga", "brand": "Genérico", "cost": 25},
    {"sku": "650240006623", "title": "Condones M Bi-Orgásmo", "brand": "M", "cost": 75},
    {"sku": "650240009525", "title": "Condones M Cosquilludo c/3", "brand": "M", "cost": 75},
    {"sku": "650240013850", "title": "Teatrical Azul 52g", "brand": "Teatrical", "cost": 40},
    {"sku": "650240013874", "title": "Teatrical Azul 230g", "brand": "Teatrical", "cost": 110},
    {"sku": "650240013881", "title": "Teatrical Azul 400g", "brand": "Teatrical", "cost": 175},
    {"sku": "650240013898", "title": "Teatrical Rosa 52g", "brand": "Teatrical", "cost": 40},
    {"sku": "650240013911", "title": "Teatrical Rosa 230g", "brand": "Teatrical", "cost": 110},
    {"sku": "650240013928", "title": "Teatrical Rosa 400g", "brand": "Teatrical", "cost": 175},
    {"sku": "650240030536", "title": "Crema Goicoechea para Diabetes", "brand": "Goicoechea", "cost": 185},
    {"sku": "650240032356", "title": "Crema Goicoechea", "brand": "Goicoechea", "cost": 175},
    {"sku": "6910021007206", "title": "Cepillo Colgate Medio", "brand": "Colgate", "cost": 20},
    {"sku": "75000950", "title": "Lata Nivea", "brand": "Nivea", "cost": 25},
    {"sku": "75001865", "title": "Brillantina Palmolive 115ml", "brand": "Palmolive", "cost": 65},
    {"sku": "75001872", "title": "Brillantina Palmolive 52ml", "brand": "Palmolive", "cost": 35},
    {"sku": "75002794", "title": "Palmolive 200ml", "brand": "Palmolive", "cost": 40},
    {"sku": "7500435019958", "title": "H&S Limpieza Renovadora 180ml", "brand": "H&S", "cost": 50},
    {"sku": "7500435020008", "title": "H&S Limpieza Renovadora 375ml", "brand": "H&S", "cost": 95},
    {"sku": "7500435154420", "title": "Gillette Prestobarba 2", "brand": "Gillette", "cost": 20},
    {"sku": "7500435162265", "title": "H&S Limpieza Renovadora 650ml", "brand": "H&S", "cost": 145},
    {"sku": "7500435168991", "title": "Espuma Azul Herbal", "brand": "Genérico", "cost": 75},
    {"sku": "7500435169035", "title": "Espuma Roja Herbal", "brand": "Genérico", "cost": 75},
    {"sku": "7500435191425", "title": "Pantene Colageno 300ml", "brand": "Pantene", "cost": 85},
    {"sku": "7500435231244", "title": "H&S Anticomezón", "brand": "H&S", "cost": 55},
    {"sku": "7500462933739", "title": "Derm Crema 240ml ADN", "brand": "Derm", "cost": 110},
    {"sku": "7501001164003", "title": "Old Spice Barra Pure Sport", "brand": "Old Spice", "cost": 70},
    {"sku": "7501001303464", "title": "Pantene Control Caída 400ml", "brand": "Pantene", "cost": 95},
    {"sku": "7501006711387", "title": "Colgate Cepillo 2 Pack", "brand": "Colgate", "cost": 55},
    {"sku": "7501006719932", "title": "Cepillo Oral B Duo Medio", "brand": "Oral B", "cost": 55},
    {"sku": "7501006721317", "title": "Pantene Restauración 400ml", "brand": "Pantene", "cost": 95},
    {"sku": "7501007528427", "title": "Lubriderm 400ml Dorada", "brand": "Lubriderm", "cost": 110},
    {"sku": "7501007528939", "title": "Lubriderm 120ml Dorada", "brand": "Lubriderm", "cost": 40},
    {"sku": "7501015903315", "title": "Cutex 50ml", "brand": "Cutex", "cost": 25},
    {"sku": "7501015903346", "title": "Cutex 100ml", "brand": "Cutex", "cost": 40},
    {"sku": "7501017361113", "title": "Kleenex Caja c/180", "brand": "Kleenex", "cost": 60},
    {"sku": "7501017362950", "title": "Kleenex Bolsillo", "brand": "Kleenex", "cost": 10},
    {"sku": "7501017366316", "title": "Suavelastic Etapa Jumbo c/14", "brand": "Suavelastic", "cost": 95},
    {"sku": "7501017367337", "title": "Kleenex Caja c/66 Aceite Humectante", "brand": "Kleenex", "cost": 75},
    {"sku": "7501017371198", "title": "Kotex Toallas sin Alas", "brand": "Kotex", "cost": 20},
    {"sku": "7501017372737", "title": "Absorsec Etapa 4 Grande c/40", "brand": "Absorsec", "cost": 160},
    {"sku": "7501017372775", "title": "Absorsec Etapa 5 Jumbo c/40", "brand": "Absorsec", "cost": 195},
    {"sku": "7501017375189", "title": "Absorsec Etapa 4 Grande c/14", "brand": "Absorsec", "cost": 80},
    {"sku": "7501019006074", "title": "Saba Intima Clip con Alas", "brand": "Saba", "cost": 20},
    {"sku": "7501019006104", "title": "Saba Intima Reg sin Alas", "brand": "Saba", "cost": 20},
    {"sku": "7501019006296", "title": "Saba Ultrainvisible c/10", "brand": "Saba", "cost": 35},
    {"sku": "7501019006647", "title": "Saba Buenas Noches Ultra Invisible c/10", "brand": "Saba", "cost": 40},
    {"sku": "7501019039966", "title": "Saba Ultra Invisible Buenas Noches c/8", "brand": "Saba", "cost": 40},
    {"sku": "7501019050664", "title": "Saba Buenas Noches c/8", "brand": "Saba", "cost": 35},
    {"sku": "7501019050671", "title": "Saba Invisible c/10", "brand": "Saba", "cost": 35},
    {"sku": "7501019068515", "title": "Saba Diarios Reg c/28", "brand": "Saba", "cost": 40},
    {"sku": "7501019068911", "title": "Saba Diarios Largo c/28", "brand": "Saba", "cost": 40},
    {"sku": "7501020921922", "title": "PM Doria Grey Natural CH", "brand": "Doria", "cost": 50},
    {"sku": "7501020940176", "title": "PM Dorian Grey Juvenil CH", "brand": "Dorian Grey", "cost": 50},
    {"sku": "7501022103111", "title": "Ricitos de Oro Manzanilla 100ml", "brand": "Ricitos de Oro", "cost": 45},
    {"sku": "7501022103166", "title": "Ricitos de Oro Manzanilla 250ml", "brand": "Ricitos de Oro", "cost": 95},
    {"sku": "7501022105191", "title": "Neutro Grisi Chico", "brand": "Grisi", "cost": 25},
    {"sku": "7501022105207", "title": "Neutro Grisi Grande", "brand": "Grisi", "cost": 30},
    {"sku": "7501022130063", "title": "Ricitos de Oro Miel y Argan", "brand": "Ricitos de Oro", "cost": 45},
    {"sku": "7501022133118", "title": "Ricitos de Oro Azul 250ml", "brand": "Ricitos de Oro", "cost": 95},
    {"sku": "7501022133286", "title": "Ricitos de Oro Miel Argan 250ml", "brand": "Ricitos de Oro", "cost": 95},
    {"sku": "7501022150801", "title": "Grisi Avena", "brand": "Grisi", "cost": 40},
    {"sku": "7501022150818", "title": "Concha Nacar Grisi", "brand": "Grisi", "cost": 45},
    {"sku": "7501027250612", "title": "Obao Roll On Piel Delicada Gris", "brand": "Obao", "cost": 42},
    {"sku": "7501027254436", "title": "Obao Frescura Intensa Naranja", "brand": "Obao", "cost": 42},
    {"sku": "7501027278487", "title": "Obao Roll On Frescula Suave Morado", "brand": "Obao", "cost": 42},
    {"sku": "7501027512758", "title": "Mamila Chica 2 oz", "brand": "Mamila", "cost": 25},
    {"sku": "7501027513021", "title": "Mamila Mediana 4 oz", "brand": "Mamila", "cost": 30},
    {"sku": "7501027514103", "title": "Mamila Grande 8 oz", "brand": "Mamila", "cost": 35},
    {"sku": "7501027524140", "title": "Mamila de Silicon", "brand": "Mamila", "cost": 14},
    {"sku": "7501027567062", "title": "Protectores para Lactancia Caja c/30", "brand": "Genérico", "cost": 95},
    {"sku": "7501032911539", "title": "Crema Repelente Off 60g", "brand": "Off", "cost": 55},
    {"sku": "7501032918392", "title": "Crema Repelente Off 198g", "brand": "Off", "cost": 115},
    {"sku": "7501032927202", "title": "Repelente Aerosol Off", "brand": "Off", "cost": 120},
    {"sku": "7501035908116", "title": "Talco Mennen Chico Azul", "brand": "Mennen", "cost": 55},
    {"sku": "7501035908123", "title": "Talco Mennen Chico Rosa", "brand": "Mennen", "cost": 55},
    {"sku": "7501035908130", "title": "Talco Mennen Grande Azul", "brand": "Mennen", "cost": 95},
    {"sku": "7501035908147", "title": "Talco Mennen Grande Rosa", "brand": "Mennen", "cost": 95},
    {"sku": "7501035908239", "title": "Aceite Mennen 50ml", "brand": "Mennen", "cost": 35},
    {"sku": "7501035908246", "title": "Aceite Mennen 100ml", "brand": "Mennen", "cost": 50},
    {"sku": "7501035908253", "title": "Aceite Mennen 200ml", "brand": "Mennen", "cost": 75},
    {"sku": "7501035909007", "title": "Stefano Black Barra", "brand": "Stefano", "cost": 60},
    {"sku": "7501035909014", "title": "Stefano Barra Spazio", "brand": "Stefano", "cost": 60},
    {"sku": "7501035911369", "title": "Colgate Total 100ml", "brand": "Colgate", "cost": 65},
    {"sku": "7501035911376", "title": "Colgate Total 150ml", "brand": "Colgate", "cost": 95},
    {"sku": "7501035911567", "title": "Pasta Colgate 50ml", "brand": "Colgate", "cost": 22},
    {"sku": "7501035914063", "title": "Wildroot Clasico 250ml", "brand": "Wildroot", "cost": 95},
    {"sku": "7501035914070", "title": "Wildroot Clasico 100ml", "brand": "Wildroot", "cost": 55},
    {"sku": "7501035919129", "title": "Palmolive 400ml", "brand": "Palmolive", "cost": 70},
    {"sku": "7501048351039", "title": "Gel Anticeptico 50ml Protec", "brand": "Protec", "cost": 18},
    {"sku": "7501048621408", "title": "Toeundas Protec c/150pz", "brand": "Protec", "cost": 30},
    {"sku": "7501048623006", "title": "Pads Facial Protec", "brand": "Protec", "cost": 40},
    {"sku": "7501054500193", "title": "Nivea Tarro 200ml", "brand": "Nivea", "cost": 110},
    {"sku": "7501054500216", "title": "Nivea Tarro 400ml", "brand": "Nivea", "cost": 190},
    {"sku": "7501054500254", "title": "Crema Nivea 500 ml", "brand": "Nivea", "cost": 210},
    {"sku": "7501054502777", "title": "Labello Cereza", "brand": "Labello", "cost": 75},
    {"sku": "7501054503095", "title": "Nivea 100ml", "brand": "Nivea", "cost": 75},
    {"sku": "7501054504535", "title": "Nivea Botella 400ml", "brand": "Nivea", "cost": 110},
    {"sku": "7501054504870", "title": "Labello Original", "brand": "Labello", "cost": 75},
    {"sku": "7501054507901", "title": "Labello Fresa", "brand": "Labello", "cost": 75},
    {"sku": "7501054549796", "title": "Nivea Botella 100ml", "brand": "Nivea", "cost": 40},
    {"sku": "7501054549802", "title": "Nivea Botella 220ml", "brand": "Nivea", "cost": 55},
    {"sku": "7501056325442", "title": "Ponds Azul 50g", "brand": "Ponds", "cost": 50},
    {"sku": "7501056326142", "title": "Ponds Azul 100g", "brand": "Ponds", "cost": 65},
    {"sku": "7501056326166", "title": "Ponds Azul 200g", "brand": "Ponds", "cost": 115},
    {"sku": "7501056326173", "title": "Ponds Azul 400g", "brand": "Ponds", "cost": 165},
    {"sku": "7501056330255", "title": "Ponds Rosa 50g", "brand": "Ponds", "cost": 60},
    {"sku": "7501056330262", "title": "Ponds Rosa 100g", "brand": "Ponds", "cost": 85},
    {"sku": "7501056330279", "title": "Ponds Rosa 200g", "brand": "Ponds", "cost": 135},
    {"sku": "7501056330309", "title": "Ponds Rosa 100g Clarant B3 Piel Balanceada Grasa", "brand": "Ponds", "cost": 85},
    {"sku": "7501056330491", "title": "Ponds Roja 100g", "brand": "Ponds", "cost": 110},
    {"sku": "7501056340025", "title": "Crema para Peinar Sedal Naranja", "brand": "Sedal", "cost": 55},
    {"sku": "7501056340100", "title": "Crema para Peinar Sedal Verde Sabila", "brand": "Sedal", "cost": 55},
    {"sku": "7501056340117", "title": "Crema para Peinar Sedal Morada", "brand": "Sedal", "cost": 55},
    {"sku": "7501056340124", "title": "Crema para Peinar Sedal Rosa", "brand": "Sedal", "cost": 55},
    {"sku": "7501056340131", "title": "Crema para Peinar Sedal Verde Menta", "brand": "Sedal", "cost": 55},
    {"sku": "7501056360412", "title": "Talco Rexona Efficiente 100g", "brand": "Rexona", "cost": 55},
    {"sku": "7501056360429", "title": "Talco Rexona Efficiente 200g", "brand": "Rexona", "cost": 95},
    {"sku": "7501058367129", "title": "Sico Safety", "brand": "Sico", "cost": 65},
    {"sku": "7501058368126", "title": "Sico Sensitive", "brand": "Sico", "cost": 65},
    {"sku": "7501061812012", "title": "Porta Cepillo Inf", "brand": "Genérico", "cost": 28},
    {"sku": "7501072600004", "title": "Orthowax Clinic", "brand": "Orthowax", "cost": 55},
    {"sku": "7501072629029", "title": "Cepillo Clinic Suave", "brand": "Clinic", "cost": 20},
    {"sku": "7501086453221", "title": "Oral B B Gengivitis 350ml", "brand": "Oral B", "cost": 220},
    {"sku": "7501086453955", "title": "Orab B Indicador 2pack", "brand": "Oral B", "cost": 55},
    {"sku": "7501086472017", "title": "Cepillo Dental Pro Doble Accion", "brand": "Genérico", "cost": 45},
    {"sku": "7501103302228", "title": "Esponja Bebe Oso Azul", "brand": "Genérico", "cost": 30},
    {"sku": "7501103303331", "title": "Esponja Redonda Bebe", "brand": "Genérico", "cost": 25},
    {"sku": "7501165009486", "title": "Latctacyd Rosa", "brand": "Lactacyd", "cost": 110},
    {"sku": "7501258209465", "title": "Protector Solar Serral 125g", "brand": "Serral", "cost": 130},
    {"sku": "7501361156007", "title": "Crema Concha Nacar 90g", "brand": "Concha Nacar", "cost": 35},
    {"sku": "7501370204577", "title": "Pinzas para Depilar Grandes", "brand": "Genérico", "cost": 22},
    {"sku": "7501370204584", "title": "Pinzas para Depilar Chicas", "brand": "Genérico", "cost": 18},
    {"sku": "7501516701052", "title": "Peine para Piojos con Lupa", "brand": "Genérico", "cost": 85},
    {"sku": "7501516704022", "title": "Peine para Piojos", "brand": "Genérico", "cost": 75},
    {"sku": "7501685170116", "title": "Softtube Sico", "brand": "Sico", "cost": 110},
    {"sku": "7501755521732", "title": "Alicatas", "brand": "Genérico", "cost": 110},
    {"sku": "7501755521817", "title": "Alicatas", "brand": "Genérico", "cost": 115},
    {"sku": "7501846501100", "title": "Cera Xiomara", "brand": "Xiomara", "cost": 65},
    {"sku": "7501943415188", "title": "Suavelastic Etapa 4 Grande c/48", "brand": "Suavelastic", "cost": 225},
    {"sku": "7501943418509", "title": "Kotex Noct c/8pz", "brand": "Kotex", "cost": 35},
    {"sku": "7501943431089", "title": "Kotex Pantiprotectores Largos", "brand": "Kotex", "cost": 45},
    {"sku": "7501943431140", "title": "Kotex Diarios c/44", "brand": "Kotex", "cost": 45},
    {"sku": "7501943431317", "title": "Kotex Pantiprotectores Reg c/22", "brand": "Kotex", "cost": 22},
    {"sku": "7501943434622", "title": "Suavelastic Etapa 2 Ch c/40", "brand": "Suavelastic", "cost": 160},
    {"sku": "7501943444928", "title": "Suavelastic Etapa 3 Med c/44", "brand": "Suavelastic", "cost": 195},
    {"sku": "7501943454743", "title": "Huggies Toallas Humedas c/80", "brand": "Huggies", "cost": 55},
    {"sku": "7501943454873", "title": "Huggies Toalla Humeda c/80 Morada", "brand": "Huggies", "cost": 55},
    {"sku": "7501943471337", "title": "Absorsec Toalla Humeda c/90", "brand": "Absorsec", "cost": 35},
    {"sku": "7501943471900", "title": "Absorsec Toalla Humeda c/120", "brand": "Absorsec", "cost": 40},
    {"sku": "7501943471962", "title": "Suavelastic Verdes", "brand": "Suavelastic", "cost": 55},
    {"sku": "7501943484214", "title": "Jabon Liquido Huggies Supreme", "brand": "Huggies", "cost": 70},
    {"sku": "7501943488922", "title": "Absorsec Etapa 6 Xjumbo c/40", "brand": "Absorsec", "cost": 215},
    {"sku": "7501943498815", "title": "Suavelastic RN c/40", "brand": "Suavelastic", "cost": 160},
    {"sku": "7502002962070", "title": "Pantimedia Natural Chica", "brand": "Pantimedia", "cost": 40},
    {"sku": "7502002962087", "title": "Pantimedia Blanca Chica", "brand": "Pantimedia", "cost": 40},
    {"sku": "7502002962094", "title": "Pantimedia Natural Grande", "brand": "Pantimedia", "cost": 40},
    {"sku": "7502002962131", "title": "Pantimedia Negra Grande", "brand": "Pantimedia", "cost": 40},
    {"sku": "7502002962193", "title": "Pantimedia Natural Med", "brand": "Pantimedia", "cost": 40},
    {"sku": "7502002962216", "title": "Pantimedia Blanca Med", "brand": "Pantimedia", "cost": 40},
    {"sku": "7502210680018", "title": "Locion 7M", "brand": "7M", "cost": 70},
    {"sku": "7502210680599", "title": "Aceite de Aguacate", "brand": "Genérico", "cost": 16},
    {"sku": "7502210680612", "title": "Aceite de Almendras Dulces", "brand": "Genérico", "cost": 16},
    {"sku": "7502210680650", "title": "Aceite de Coco", "brand": "Genérico", "cost": 16},
    {"sku": "7502210680759", "title": "Aceite de Mamey", "brand": "Genérico", "cost": 16},
    {"sku": "7502210680797", "title": "Aceite de Olivo", "brand": "Genérico", "cost": 16},
    {"sku": "7502210680896", "title": "Aceite de Romero", "brand": "Genérico", "cost": 16},
    {"sku": "75022106810158", "title": "Agua de Rosas 125 ml", "brand": "Genérico", "cost": 20},
    {"sku": "7502210681312", "title": "Pan Puerco", "brand": "Genérico", "cost": 22},
    {"sku": "7502214980015", "title": "Prudence Clasico", "brand": "Prudence", "cost": 45},
    {"sku": "7502214980275", "title": "Prudence Soda", "brand": "Prudence", "cost": 45},
    {"sku": "7502214982477", "title": "Prudence Fresa", "brand": "Prudence", "cost": 45},
    {"sku": "7502214982491", "title": "Prudence Uva", "brand": "Prudence", "cost": 45},
    {"sku": "7502214982514", "title": "Prudence Chocolate", "brand": "Prudence", "cost": 45},
    {"sku": "7502214983207", "title": "Lubricante Prudence Uva", "brand": "Prudence", "cost": 95},
    {"sku": "7502221181337", "title": "Brut Aerosol Classic", "brand": "Brut", "cost": 75},
    {"sku": "7502221181641", "title": "Brut Barra Classic", "brand": "Brut", "cost": 60},
    {"sku": "7502221184598", "title": "Brut Clasic Roll On", "brand": "Brut", "cost": 45},
    {"sku": "7502221186509", "title": "Brut Roll On Classic", "brand": "Brut", "cost": 45},
    {"sku": "7502221186998", "title": "Brut Barra Deep Blue", "brand": "Brut", "cost": 75},
    {"sku": "7502221187100", "title": "Brut Roll On 5 en 1", "brand": "Brut", "cost": 45},
    {"sku": "7502234762417", "title": "Nailex Deseterrador", "brand": "Nailex", "cost": 145},
    {"sku": "7502245720079", "title": "Silica Uva 120ml", "brand": "Silica", "cost": 55},
    {"sku": "7502245720109", "title": "Silica Uva 60ml", "brand": "Silica", "cost": 25},
    {"sku": "7502245720192", "title": "Silica Frutas", "brand": "Silica", "cost": 25},
    {"sku": "7502245720581", "title": "Silica Rosa", "brand": "Silica", "cost": 25},
    {"sku": "7502253580061", "title": "Aceite de Menta", "brand": "Genérico", "cost": 16},
    {"sku": "7502253580788", "title": "Rosa de Castilla", "brand": "Genérico", "cost": 5},
    {"sku": "7502253600516", "title": "Protector Solar Foto Sun", "brand": "Foto Sun", "cost": 125},
    {"sku": "7502269740053", "title": "Chupon para Bebe", "brand": "Genérico", "cost": 6},
    {"sku": "7502304290284", "title": "Gum Uso Diario", "brand": "Gum", "cost": 125},
    {"sku": "7503002045312", "title": "Esencia Clavo", "brand": "Genérico", "cost": 25},
    {"sku": "7503002163023", "title": "Gel Xtreme", "brand": "Xtreme", "cost": 33},
    {"sku": "7503005405168", "title": "Sacate p/Baño Saluk", "brand": "Saluk", "cost": 20},
    {"sku": "7503007859648", "title": "Blumen Jabon Liquido Cereza 525 ml", "brand": "Blumen", "cost": 65},
    {"sku": "7503019537992", "title": "Acido Hialuronico", "brand": "Genérico", "cost": 120},
    {"sku": "7503039969247", "title": "Aceite de Argan", "brand": "Genérico", "cost": 25},
    {"sku": "7506192503358", "title": "Gel Ego Magnetic", "brand": "Ego", "cost": 30},
    {"sku": "7506192505543", "title": "Crema para Peinar Sabile 300ml", "brand": "Sabile", "cost": 45},
    {"sku": "7506195132906", "title": "Oral B 250ml", "brand": "Oral B", "cost": 75},
    {"sku": "7506195148686", "title": "H&S Limpieza Renovadora 90ml", "brand": "H&S", "cost": 22},
    {"sku": "7506195158739", "title": "Natullera sin Alas c/8", "brand": "Natullera", "cost": 17},
    {"sku": "7506267911675", "title": "Blumen Jabon Liquido Manzana 525 ml", "brand": "Blumen", "cost": 65},
    {"sku": "75062897", "title": "Rexona Barra Bamboo & Aloe Vera", "brand": "Rexona", "cost": 55},
    {"sku": "75062910", "title": "Rexona Barra Active Emotion", "brand": "Rexona", "cost": 55},
    {"sku": "75062927", "title": "Rexona Barra Powder Dry", "brand": "Rexona", "cost": 55},
    {"sku": "7506295337454", "title": "Clearblue", "brand": "Clearblue", "cost": 275},
    {"sku": "7506295356776", "title": "Cepillos Pro Econo Pack c/3", "brand": "Pro", "cost": 85},
    {"sku": "7506295369387", "title": "Tampax Verde", "brand": "Tampax", "cost": 60},
    {"sku": "7506306213906", "title": "Axe Aerosol Ice Chill", "brand": "Axe", "cost": 65},
    {"sku": "7506306219922", "title": "Rexona Talco 50g", "brand": "Rexona", "cost": 35},
    {"sku": "7506306221406", "title": "Crema para Peinar Sabile 100ml", "brand": "Sabile", "cost": 25},
    {"sku": "7506306226739", "title": "Axe Aerosol", "brand": "Axe", "cost": 65},
    {"sku": "7506306244795", "title": "Ace Aerosol Intense", "brand": "Ace", "cost": 65},
    {"sku": "7506306246010", "title": "Jabon Zest Verde", "brand": "Zest", "cost": 24},
    {"sku": "7506306246096", "title": "Jabon Zest Azul", "brand": "Zest", "cost": 25},
    {"sku": "7506306247499", "title": "Gel Ego Atraction 220ml", "brand": "Ego", "cost": 30},
    {"sku": "7506306247505", "title": "Gel Ego Black 220ml", "brand": "Ego", "cost": 30},
    {"sku": "7506306249042", "title": "Vaseline Grande", "brand": "Vaseline", "cost": 70},
    {"sku": "7506306249189", "title": "Savile 700ml Nutricion", "brand": "Savile", "cost": 45},
    {"sku": "7506306249233", "title": "Savile 700ml Control Caida", "brand": "Savile", "cost": 45},
    {"sku": "7506306249240", "title": "Savile 700ml Fuerza y Reparacion", "brand": "Savile", "cost": 45},
    {"sku": "7506306249356", "title": "Vaseline Chico", "brand": "Vaseline", "cost": 38},
    {"sku": "7506309895208", "title": "Natullera con Alas c/8", "brand": "Natullera", "cost": 24},
    {"sku": "7506339349030", "title": "Old Spice Aerosol Pure Sport", "brand": "Old Spice", "cost": 75},
    {"sku": "7506339349047", "title": "Old Spice Aerosol Fresh", "brand": "Old Spice", "cost": 75},
    {"sku": "7506339390230", "title": "Old Spice Barra Leña", "brand": "Old Spice", "cost": 70},
    {"sku": "7506339394719", "title": "Naturella Nocturna c/8", "brand": "Naturella", "cost": 35},
    {"sku": "7506339395518", "title": "Gel de Afeitar Gillete", "brand": "Gillette", "cost": 145},
    {"sku": "7506346600292", "title": "Lima de Uñas", "brand": "Genérico", "cost": 2},
    {"sku": "7506346601053", "title": "Hilo Dental Menta Fresh Cool", "brand": "Genérico", "cost": 55},
    {"sku": "7506425606924", "title": "Jabon Escudo Antibacterial", "brand": "Escudo", "cost": 20},
    {"sku": "7506425607808", "title": "Huggies Supreme", "brand": "Huggies", "cost": 60},
    {"sku": "7506425625536", "title": "Cotex Tampones Rosa", "brand": "Cotex", "cost": 55},
    {"sku": "7506425625550", "title": "Cotex Tampones Morados", "brand": "Cotex", "cost": 55},
    {"sku": "7506425625574", "title": "Tampax Cotex Tampones Naranjas", "brand": "Cotex", "cost": 55},
    {"sku": "7506425633753", "title": "Suavelastic Etapa 5 Jumbo c/46", "brand": "Suavelastic", "cost": 235},
    {"sku": "7506425633777", "title": "Suavelastic Etapa 6 Xjumbo c/46", "brand": "Suavelastic", "cost": 265},
    {"sku": "7506425645749", "title": "Suavelastic Etapa 7 XXJ c/40", "brand": "Suavelastic", "cost": 285},
    {"sku": "7506425648634", "title": "Suavelastic RN c/20", "brand": "Suavelastic", "cost": 60},
    {"sku": "7506449300266", "title": "Derm Crema", "brand": "Derm", "cost": 125},
    {"sku": "7506460101514", "title": "Sico Softlube Original", "brand": "Sico", "cost": 110},
    {"sku": "75073107", "title": "Rexona Barra Clinical", "brand": "Rexona", "cost": 115},
    {"sku": "75076238", "title": "Axe Barra Apollo", "brand": "Axe", "cost": 70},
    {"sku": "75076283", "title": "Axe Barra Ice Chill", "brand": "Axe", "cost": 70},
    {"sku": "75076337", "title": "Rexona Barra Amarillo", "brand": "Rexona", "cost": 60},
    {"sku": "75076368", "title": "Rexona Barra Sport", "brand": "Rexona", "cost": 60},
    {"sku": "75076559", "title": "Axe Barra Dark Temptation", "brand": "Axe", "cost": 70},
    {"sku": "7508304330098", "title": "Pasadores", "brand": "Genérico", "cost": 18},
    {"sku": "7509546000343", "title": "Colgate Triple Accion 100ml", "brand": "Colgate", "cost": 45},
    {"sku": "7509546000985", "title": "Colgate Triple Accion 75ml", "brand": "Colgate", "cost": 35},
    {"sku": "7509546015545", "title": "Lady Speed Stick Barra Active", "brand": "Speed Stick", "cost": 75},
    {"sku": "7509546017389", "title": "Palmolive 700ml", "brand": "Palmolive", "cost": 95},
    {"sku": "7509546029139", "title": "Speed Stick Gel", "brand": "Speed Stick", "cost": 75},
    {"sku": "7509546039152", "title": "Pasta Colgate 22ml", "brand": "Colgate", "cost": 20},
    {"sku": "7509546045313", "title": "Speed Stick Gel Xtreme Intense", "brand": "Speed Stick", "cost": 65},
    {"sku": "7509546052755", "title": "Speed Stick Gel 24/7", "brand": "Speed Stick", "cost": 65},
    {"sku": "7509546052885", "title": "Kit Portatil Colgate", "brand": "Colgate", "cost": 95},
    {"sku": "7509546056432", "title": "Speed Stick Azul Gel", "brand": "Speed Stick", "cost": 75},
    {"sku": "7509546058962", "title": "Spray Cabrice Verde", "brand": "Cabrice", "cost": 50},
    {"sku": "7509546058979", "title": "Spray Cabrice Azul", "brand": "Cabrice", "cost": 50},
    {"sku": "7509546058986", "title": "Spray Caprice Morado", "brand": "Caprice", "cost": 50},
    {"sku": "7509546060460", "title": "Lady Speed Stick 24/7", "brand": "Speed Stick", "cost": 65},
    {"sku": "7509546060477", "title": "Speed Stick Roll On Powder Fresh", "brand": "Speed Stick", "cost": 40},
    {"sku": "7509546061504", "title": "Speed Stick Gel Stress Defense", "brand": "Speed Stick", "cost": 75},
    {"sku": "7509546061665", "title": "Speed Stick Gel Xtreme Intense", "brand": "Speed Stick", "cost": 75},
    {"sku": "7509546063515", "title": "Lady Speed Stick Pro 5", "brand": "Speed Stick", "cost": 70},
    {"sku": "7509546063706", "title": "Speed Stick Aerosol Xtreme Ultra", "brand": "Speed Stick", "cost": 75},
    {"sku": "7509546063843", "title": "Lady Speed Stick Aerosol Pro 5", "brand": "Speed Stick", "cost": 70},
    {"sku": "7509546063867", "title": "Speed Stick Aerosol Xtreme Intense", "brand": "Speed Stick", "cost": 75},
    {"sku": "7509546068619", "title": "Stefano Aerosol Imperial", "brand": "Stefano", "cost": 65},
    {"sku": "7509546068909", "title": "Colgate Triple Accion 50ml", "brand": "Colgate", "cost": 20},
    {"sku": "7509546072050", "title": "Mennen Protecion 200ml", "brand": "Mennen", "cost": 40},
    {"sku": "7509546072074", "title": "Mennen Proteccion Shampo 700ml", "brand": "Mennen", "cost": 85},
    {"sku": "7509546072272", "title": "Colgate Kids 50g", "brand": "Colgate", "cost": 35},
    {"sku": "7509546073453", "title": "Cepillo Colgate 2 Pack Kids", "brand": "Colgate", "cost": 55},
    {"sku": "7509546073767", "title": "Stefano Aerosol Black", "brand": "Stefano", "cost": 65},
    {"sku": "7509546073774", "title": "Stefano Aerosol Spazio", "brand": "Stefano", "cost": 65},
    {"sku": "7509546074504", "title": "Mennen Shampo Zero", "brand": "Mennen", "cost": 70},
    {"sku": "7509546687353", "title": "Pasta Colgate 90ml", "brand": "Colgate", "cost": 45},
    {"sku": "7509552847987", "title": "Elvive Reparacion Total 5", "brand": "Elvive", "cost": 75},
    {"sku": "7590002046234", "title": "Natullera Protectores c/40", "brand": "Natullera", "cost": 45},
    {"sku": "759684272103", "title": "Cotonetes Grande c/100", "brand": "Cotonetes", "cost": 24},
    {"sku": "759684273094", "title": "Cotonetes Chicos c/50", "brand": "Cotonetes", "cost": 15},
    {"sku": "7702018013326", "title": "Espuma para Afeitar Sensitive", "brand": "Genérico", "cost": 115},
    {"sku": "7702018053469", "title": "Espuma para Afeitar Mentol Gillete", "brand": "Gillette", "cost": 115},
    {"sku": "7702018072439", "title": "Rastrillo Venus", "brand": "Venus", "cost": 40},
    {"sku": "7702018880409", "title": "Gillette Prestobarba 3", "brand": "Gillette", "cost": 28},
    {"sku": "7702031244486", "title": "Lubriderm 120ml Azul", "brand": "Lubriderm", "cost": 40},
    {"sku": "7702031244493", "title": "Lubriderm 200ml Azul", "brand": "Lubriderm", "cost": 55},
    {"sku": "7702031244509", "title": "Lubriderm 400ml Azul", "brand": "Lubriderm", "cost": 110},
    {"sku": "7702031244783", "title": "Listerine Ultra Clean", "brand": "Listerine", "cost": 75},
    {"sku": "7702031291510", "title": "Johnsons Amarillo", "brand": "Johnson's", "cost": 130},
    {"sku": "7702031293538", "title": "Johnsons Azul", "brand": "Johnson's", "cost": 130},
    {"sku": "7702031887928", "title": "Listerine Cuidado Total", "brand": "Listerine", "cost": 75},
    {"sku": "7702035416155", "title": "Lubriderm 200ml Morada", "brand": "Lubriderm", "cost": 55},
    {"sku": "7702035457639", "title": "Lubriderm 400ml Morada", "brand": "Lubriderm", "cost": 110},
    {"sku": "7702035469151", "title": "Lubriderm 120ml Morada", "brand": "Lubriderm", "cost": 40},
    {"sku": "7702035870384", "title": "Lubriderm 200ml Dorada", "brand": "Lubriderm", "cost": 55},
    {"sku": "7791293022567", "title": "Rexona Aerosol V8", "brand": "Rexona", "cost": 75},
    {"sku": "7791293025537", "title": "Rexona Aerosol Antibacterial Protecion", "brand": "Rexona", "cost": 75},
    {"sku": "7791293025780", "title": "Ace Aerosol Apollo", "brand": "Ace", "cost": 65},
    {"sku": "7791293025797", "title": "Ace Aerosol Dark Temptation", "brand": "Ace", "cost": 65},
    {"sku": "7791293025810", "title": "Ace Aerosol Fusion", "brand": "Ace", "cost": 65},
    {"sku": "7791293032436", "title": "Rexona Aerosol Powder Dry", "brand": "Rexona", "cost": 75},
    {"sku": "7791293032443", "title": "Rexona Aerosol Active Emotion", "brand": "Rexona", "cost": 75},
    {"sku": "7791293032450", "title": "Rexona Aerosol Bamboo & Aloe Vera", "brand": "Rexona", "cost": 75},
    {"sku": "7794640170133", "title": "Sensodyne", "brand": "Sensodyne", "cost": 155},
    {"sku": "7891010974329", "title": "Listerine Cool Mint sin Azucar", "brand": "Listerine", "cost": 75},
    {"sku": "7891024183182", "title": "Colgate Hilo Dental", "brand": "Colgate", "cost": 95},
    {"sku": "78924338", "title": "Rexona Roll On Powder Dry", "brand": "Rexona", "cost": 55},
    {"sku": "78924345", "title": "Rexona Roll On Bamboo & Aloe Vera", "brand": "Rexona", "cost": 55},
    {"sku": "78924574", "title": "Axe Roll On Dark Temptation", "brand": "Axe", "cost": 45},
    {"sku": "78926523", "title": "Rexona Roll On Active Emotion", "brand": "Rexona", "cost": 55},
    {"sku": "7896009419324", "title": "Sensodyne Original 90g", "brand": "Sensodyne", "cost": 110},
    {"sku": "7896009490651", "title": "Corega Sin Sabor", "brand": "Corega", "cost": 175},
    {"sku": "7896090611676", "title": "Sensodyne Antisarro", "brand": "Sensodyne", "cost": 125},
    {"sku": "7898909175539", "title": "Cateter #24", "brand": "Genérico", "cost": 23},
    {"sku": "793969378180", "title": "Esponja para Baño Rana Bebe", "brand": "Genérico", "cost": 30},
    {"sku": "793969378241", "title": "Contador de Pastillas", "brand": "Genérico", "cost": 55},
    {"sku": "793969378258", "title": "Cepillo Dental Bebe", "brand": "Genérico", "cost": 50},
    {"sku": "810120501628", "title": "Grisi Azufre", "brand": "Grisi", "cost": 55},
    {"sku": "8886467137143", "title": "Babydove", "brand": "Dove", "cost": 40},
    {"sku": "90225003", "title": "Crema Enumi", "brand": "Enumi", "cost": 425},
    {"sku": "CL", "title": "Esencia de Clavo", "brand": "Genérico", "cost": 25},
    {"sku": "CPM", "title": "Chupones para Mamila", "brand": "Genérico", "cost": 12},
    {"sku": "LN", "title": "Lima de Uñas Paquete", "brand": "Genérico", "cost": 35},
    {"sku": "LNS", "title": "Lima de Uñas Suelta", "brand": "Genérico", "cost": 8},
    {"sku": "PE", "title": "Peine", "brand": "Genérico", "cost": 30},
    {"sku": "PP", "title": "Peine para Piojos Plastico", "brand": "Genérico", "cost": 10},
    {"sku": "QC", "title": "Quita Callos", "brand": "Genérico", "cost": 20},
    {"sku": "RA", "title": "Rastrillo Armable", "brand": "Genérico", "cost": 20},
    {"sku": "7502253580818", "title": "Alumbre en Trozo", "brand": "Genérico", "cost": 5},
    {"sku": "7502276040597", "title": "Mexana Talco 80g", "brand": "Mexana", "cost": 65},
    {"sku": "7502276040603", "title": "Mexana Talco 160", "brand": "Mexana", "cost": 125},
    {"sku": "650240007750", "title": "Silka Talco", "brand": "Silka", "cost": 145},
    {"sku": "650240007828", "title": "Asepxia Azufre", "brand": "Asepxia", "cost": 55},
    {"sku": "7503013457302", "title": "Zero Piojos Shampoo", "brand": "Zero Piojos", "cost": 185}
]


# ---------------------------
# Helpers
# ---------------------------

def get_or_create_brand(db: Session, name: str) -> int:
    brand = db.query(ProductBrand).filter_by(name=name).first()
    if not brand:
        brand = ProductBrand(name=name)
        db.add(brand)
        db.commit()
        db.refresh(brand)
    return brand.id


def get_or_create_category(db: Session, name: str, parent_name: str | None = None) -> int:
    parent = None
    if parent_name:
        parent = db.query(ProductCategory).filter_by(name=parent_name).first()
        if not parent:
            parent = ProductCategory(name=parent_name)
            db.add(parent)
            db.commit()
            db.refresh(parent)

    category = db.query(ProductCategory).filter_by(name=name).first()
    if not category:
        category = ProductCategory(name=name, parent_id=parent.id if parent else None)
        db.add(category)
        db.commit()
        db.refresh(category)

    return category.id


# ---------------------------
# Seeder principal
# ---------------------------

def seed_salud_belleza(db: Session):

    try:
        # ROOT
        root_id = get_or_create_category(db, "Salud y belleza")

        # SUBCATEGORÍAS
        higiene_id = get_or_create_category(db, "Higiene personal", "Salud y belleza")
        cuidado_piel_id = get_or_create_category(db, "Cuidado de la piel", "Salud y belleza")
        cabello_id = get_or_create_category(db, "Cabello", "Salud y belleza")
        dental_id = get_or_create_category(db, "Higiene dental", "Salud y belleza")
        sexual_id = get_or_create_category(db, "Salud sexual", "Salud y belleza")
        bebe_id = get_or_create_category(db, "Bebé y maternidad", "Salud y belleza")
        herramientas_id = get_or_create_category(db, "Accesorios y herramientas", "Salud y belleza")
        farmacia_id = get_or_create_category(db, "Dispositivos médicos", "Salud y belleza")
        otros_id = get_or_create_category(db, "Otros belleza", None)

        created = 0
        skipped = 0

        for item in SALUD_BELLEZA:
            if db.query(Product).filter_by(sku=item["sku"]).first():
                skipped += 1
                continue

            brand_id = get_or_create_brand(db, item["brand"])
            title = item["title"].lower()

            # Clasificación automática
            if any(x in title for x in ["jabón", "desodorante", "talco", "nivea", "ponds", "lubriderm"]):
                category_id = cuidado_piel_id
            elif any(x in title for x in ["pantene", "shampoo", "savile", "elvive", "head", "sedal"]):
                category_id = cabello_id
            elif any(x in title for x in ["colgate", "listerine", "sensodyne", "cepillo", "hilo dental"]):
                category_id = dental_id
            elif any(x in title for x in ["condón", "prudence", "sico"]):
                category_id = sexual_id
            elif any(x in title for x in ["bebé", "chupón", "mamila", "huggies"]):
                category_id = bebe_id
            elif any(x in title for x in ["uña", "pinza", "alicate", "lima", "quita callos"]):
                category_id = herramientas_id
            elif any(x in title for x in ["catéter", "contador", "dispositivo"]):
                category_id = farmacia_id
            else:
                category_id = higiene_id

            cost = float(item["cost"])
            retail = round(cost * 1.40, 2)

            product = Product(
                title=item["title"],
                sku=item["sku"],
                brand_id=brand_id,
                product_category_id=category_id,
                price_cost=cost,
                price_retail=retail,
                unit_name="pieza",
                is_unit_sale=True,
                description="Producto salud y belleza precargado",
            )

            db.add(product)
            created += 1

        db.commit()
        print(f"✅ Salud y belleza insertados: {created}")
        print(f"⚠️ Duplicados omitidos: {skipped}")

    except Exception as e:
        db.rollback()
        raise e


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_salud_belleza(db)
    finally:
        db.close()