// Real names. Format: "Name|gender|culture|language|religions|meaning|story"
// gender: g = girl, b = boy, e = either. Religions are comma-separated (blank = none in particular).
const REAL_RAW = `
Alexander|b|Greek|Greek||defender of the people|Alexander the Great
Alexandra|g|Greek|Greek||defender of the people|
Andreas|b|Greek|Greek|Christian|manly, brave|Greek form of Andrew the Apostle
Christos|b|Greek|Greek|Christian|the anointed one|
Dimitrios|b|Greek|Greek||devoted to Demeter|
Eleni|g|Greek|Greek||torch, bright light|Greek form of Helen
Georgios|b|Greek|Greek|Christian|farmer|Saint George
Irene|g|Greek|Greek||peace|Eirene, goddess of peace
Katerina|g|Greek|Greek|Christian|pure|Saint Catherine
Konstantinos|b|Greek|Greek|Christian|steadfast, constant|Emperor Constantine
Nikolaos|b|Greek|Greek|Christian|victory of the people|Saint Nicholas
Panagiotis|b|Greek|Greek|Christian|all-holy|
Sophia|g|Greek|Greek|Christian|wisdom|Hagia Sophia
Theodora|g|Greek|Greek|Christian|gift of God|Empress Theodora
Theodore|b|Greek|Greek|Christian|gift of God|
Stavros|b|Greek|Greek|Christian|cross|
Anastasia|g|Greek|Greek|Christian|resurrection|
Kyriaki|g|Greek|Greek|Christian|of the Lord; Sunday|
Despina|g|Greek|Greek||lady|
Yiannis|b|Greek|Greek|Christian|God is gracious|Greek form of John
Evangelia|g|Greek|Greek|Christian|good news|
Petros|b|Greek|Greek|Christian|rock|Peter the Apostle
Stephanos|b|Greek|Greek|Christian|crown|Saint Stephen, the first martyr
Kosmas|b|Greek|Greek|Christian|order, beauty|Saint Kosmas
Zoe|g|Greek|Greek||life|
Chloe|g|Greek|Greek|Christian|green shoot|mentioned by Paul in 1 Corinthians
Eugenia|g|Greek|Greek||well-born|
Leander|b|Greek|Greek|Greek myth|lion-man|swam the Hellespont for Hero
Phoebe|g|Greek|Greek|Greek myth,Christian|bright, radiant|a Titan; also a deacon in Romans
Penelope|g|Greek|Greek|Greek myth|weaver|faithful wife of Odysseus
Athena|g|Greek|Greek|Greek myth||goddess of wisdom and courage
Artemis|g|Greek|Greek|Greek myth||goddess of the hunt and the moon
Apollo|b|Greek|Greek|Greek myth||god of the sun, music and healing
Hermes|b|Greek|Greek|Greek myth||messenger of the gods
Achilles|b|Greek|Greek|Greek myth||greatest hero of the Trojan War
Hector|b|Greek|Greek|Greek myth|holding fast|prince and defender of Troy
Persephone|g|Greek|Greek|Greek myth||queen of the underworld, goddess of spring
Calliope|g|Greek|Greek|Greek myth|beautiful voice|muse of epic poetry
Cassandra|g|Greek|Greek|Greek myth||prophetess of Troy
Daphne|g|Greek|Greek|Greek myth|laurel|nymph who became a laurel tree
Iris|g|Greek|Greek|Greek myth|rainbow|goddess of the rainbow
Selene|g|Greek|Greek|Greek myth|moon|goddess of the moon
Helios|b|Greek|Greek|Greek myth|sun|god of the sun
Atlas|b|Greek|Greek|Greek myth|to endure|Titan who holds up the sky
Orion|b|Greek|Greek|Greek myth||great hunter, now a constellation
Jason|b|Greek|Greek|Greek myth|healer|leader of the Argonauts
Thalia|g|Greek|Greek|Greek myth|to flourish|muse of comedy
Andromeda|g|Greek|Greek|Greek myth||princess rescued by Perseus
Perseus|b|Greek|Greek|Greek myth||hero who defeated Medusa
Ariadne|g|Greek|Greek|Greek myth|most holy|helped Theseus escape the labyrinth
Hera|g|Greek|Greek|Greek myth||queen of the gods
Theseus|b|Greek|Greek|Greek myth||slayer of the Minotaur
Xander|b|Greek|Greek||defender of the people|short for Alexander
Philip|b|Greek|Greek|Christian|lover of horses|Philip the Apostle
Timothy|b|Greek|Greek|Christian|honoring God|companion of Paul
Lydia|g|Greek|Greek|Christian|woman from Lydia|first European convert in Acts
Luke|b|Greek|Greek|Christian|from Lucania|author of the Gospel of Luke
Aarav|b|Indian|Sanskrit||peaceful, calm|
Anand|b|Indian|Sanskrit|Hindu|joy, bliss|
Arjun|b|Indian|Sanskrit|Hindu|bright, shining|archer hero of the Mahabharata
Krishna|b|Indian|Sanskrit|Hindu|dark, all-attractive|avatar of Vishnu, speaker of the Bhagavad Gita
Ram|b|Indian|Sanskrit|Hindu|pleasing|hero of the Ramayana
Sita|g|Indian|Sanskrit|Hindu|furrow|heroine of the Ramayana
Lakshman|b|Indian|Sanskrit|Hindu|marked with good signs|loyal brother of Rama
Ganesh|b|Indian|Sanskrit|Hindu|lord of the people|elephant-headed god of new beginnings
Shiva|b|Indian|Sanskrit|Hindu|auspicious|one of the principal Hindu gods
Parvati|g|Indian|Sanskrit|Hindu|daughter of the mountain|goddess, consort of Shiva
Lakshmi|g|Indian|Sanskrit|Hindu|sign, good fortune|goddess of wealth and prosperity
Saraswati|g|Indian|Sanskrit|Hindu|flowing one|goddess of knowledge and music
Durga|g|Indian|Sanskrit|Hindu|invincible|warrior goddess
Radha|g|Indian|Sanskrit|Hindu|prosperity, success|beloved of Krishna
Draupadi|g|Indian|Sanskrit|Hindu||heroine of the Mahabharata
Gauri|g|Indian|Sanskrit|Hindu|fair, bright|a name of Parvati
Uma|g|Indian|Sanskrit|Hindu|tranquility|a name of Parvati
Meera|g|Indian|Sanskrit|Hindu|devoted one|Mirabai, poet-saint devoted to Krishna
Ananya|g|Indian|Sanskrit||unique, matchless|
Aditi|g|Indian|Sanskrit|Hindu|boundless|mother of the gods in the Vedas
Aditya|b|Indian|Sanskrit|Hindu|son of Aditi; the sun|
Vishnu|b|Indian|Sanskrit|Hindu|all-pervading|preserver of the universe
Indra|b|Indian|Sanskrit|Hindu||king of the gods in the Vedas
Surya|b|Indian|Sanskrit|Hindu|sun|the sun god
Chandra|b|Indian|Sanskrit|Hindu|moon|the moon god
Dev|b|Indian|Sanskrit|Hindu|god, divine|
Ishaan|b|Indian|Sanskrit|Hindu|lord; northeast|a name of Shiva
Rohan|b|Indian|Sanskrit||ascending|
Vikram|b|Indian|Sanskrit||valor|King Vikramaditya
Nakul|b|Indian|Sanskrit|Hindu||one of the five Pandava brothers
Karan|b|Indian|Sanskrit|Hindu||after Karna, warrior of the Mahabharata
Yash|b|Indian|Sanskrit||fame, glory|
Neel|b|Indian|Sanskrit||blue|
Riya|g|Indian|Sanskrit||singer|
Priya|g|Indian|Sanskrit||beloved|
Diya|g|Indian|Sanskrit|Hindu|lamp|lit at Diwali
Kavya|g|Indian|Sanskrit||poetry|
Isha|g|Indian|Sanskrit|Hindu|goddess, ruler|
Tara|g|Indian|Sanskrit|Hindu,Buddhist|star|goddess in Hindu and Buddhist tradition
Nandini|g|Indian|Sanskrit|Hindu|giver of joy|the sacred wish-granting cow
Ganga|g|Indian|Sanskrit|Hindu||the sacred river Ganges
Yamuna|g|Indian|Sanskrit|Hindu||sacred river, beloved of Krishna
Shanti|g|Indian|Sanskrit|Hindu,Buddhist|peace|
Asha|g|Indian|Sanskrit||hope|
Jaya|g|Indian|Sanskrit||victory|
Leela|g|Indian|Sanskrit|Hindu|divine play|
Pooja|g|Indian|Sanskrit|Hindu|worship|
Arya|e|Indian|Sanskrit||noble|
Veda|g|Indian|Sanskrit|Hindu|knowledge|the Vedas, Hinduism's oldest scriptures
Aryan|b|Indian|Sanskrit||noble|
Siddharth|b|Indian|Sanskrit|Buddhist,Hindu|one who has achieved his goal|birth name of the Buddha
Gautam|b|Indian|Sanskrit|Buddhist||family name of the Buddha
Ananda|b|Indian|Sanskrit|Buddhist|joy, bliss|the Buddha's closest disciple
Bodhi|e|Indian|Sanskrit|Buddhist|enlightenment|the Bodhi tree where the Buddha awoke
Maya|g|Indian|Sanskrit|Buddhist,Hindu|illusion, magic|Written माया; Māyā, mother of the Buddha
Rahul|b|Indian|Sanskrit|Buddhist||son of the Buddha
Sujata|g|Indian|Sanskrit|Buddhist|well-born|offered rice to the Buddha before his enlightenment
Yashodhara|g|Indian|Sanskrit|Buddhist|bearer of glory|wife of the Buddha
Dharma|e|Indian|Sanskrit|Hindu,Buddhist|duty, cosmic law|
Mahavir|b|Indian|Sanskrit|Jain|great hero|24th Tirthankara of Jainism
Rishabh|b|Indian|Sanskrit|Jain|bull; the best of its kind|Written ऋषभ, from Sanskrit ṛṣabha: a bull, and the best or most excellent of any kind (as in puruṣarṣabha, “best of men”). It is also the second of the seven notes of the Indian scale (re in sa-re-ga-ma) and the name of the first of the 24 Jain Tirthankaras. (Monier-Williams Sanskrit–English Dictionary)
Chandana|g|Indian|Sanskrit|Jain|sandalwood|leader of the nuns under Mahavir
Kavin|b|Indian|Tamil||handsome, beautiful|
Anbu|e|Indian|Tamil||love|
Mugilan|b|Indian|Tamil||cloud|
Thamarai|g|Indian|Tamil||lotus|
Nila|g|Indian|Tamil||moon|
Gurpreet|e|Indian|Punjabi|Sikh|love of the Guru|
Harpreet|e|Indian|Punjabi|Sikh|love of God|
Simran|g|Indian|Punjabi|Sikh|remembrance of God|meditation in Sikh practice
Jaspreet|e|Indian|Punjabi|Sikh|love of praise|
Amrit|e|Indian|Punjabi|Sikh,Hindu|nectar of immortality|
Arjan|b|Indian|Punjabi|Sikh||Guru Arjan Dev, compiler of the Adi Granth
Nanak|b|Indian|Punjabi|Sikh||Guru Nanak, founder of Sikhism
Gobind|b|Indian|Punjabi|Sikh||Guru Gobind Singh, the tenth Guru
Harleen|g|Indian|Punjabi|Sikh|absorbed in God|
Manpreet|e|Indian|Punjabi|Sikh|love of the heart|
Navjot|e|Indian|Punjabi|Sikh|new light|
Ekam|e|Indian|Punjabi|Sikh|oneness of God|from Ik Onkar
Sukhmani|g|Indian|Punjabi|Sikh|pearl of peace|a famous Sikh prayer
Kabir|b|Indian|Arabic|Sikh,Hindu,Islamic|great|poet-saint whose verses are in the Guru Granth Sahib
Muhammad|b|Arab|Arabic|Islamic|praised|the Prophet of Islam
Ahmad|b|Arab|Arabic|Islamic|most praised|
Ali|b|Arab|Arabic|Islamic|exalted|cousin of the Prophet, fourth caliph
Umar|b|Arab|Arabic|Islamic|flourishing, long-lived|the second caliph
Hassan|b|Arab|Arabic|Islamic|handsome, good|grandson of the Prophet
Hussein|b|Arab|Arabic|Islamic|little good one|grandson of the Prophet
Ibrahim|b|Arab|Hebrew|Islamic|father of many|Prophet Abraham in the Quran
Yusuf|b|Arab|Hebrew|Islamic|God increases|Prophet Joseph; Surah Yusuf
Musa|b|Arab|Hebrew|Islamic|drawn out|Prophet Moses in the Quran
Isa|b|Arab|Hebrew|Islamic|God saves|Jesus in the Quran
Yahya|b|Arab|Hebrew|Islamic|he lives|John the Baptist in the Quran
Nuh|b|Arab|Hebrew|Islamic|rest|Prophet Noah; Surah Nuh
Idris|b|Arab|Arabic|Islamic||a prophet named in the Quran
Sulaiman|b|Arab|Hebrew|Islamic|man of peace|Prophet Solomon in the Quran
Dawud|b|Arab|Hebrew|Islamic|beloved|Prophet David in the Quran
Ismail|b|Arab|Hebrew|Islamic|God hears|son of Ibrahim
Zakariya|b|Arab|Hebrew|Islamic|God remembers|father of Yahya
Yunus|b|Arab|Hebrew|Islamic|dove|Prophet Jonah; Surah Yunus
Harun|b|Arab|Hebrew|Islamic||Prophet Aaron, brother of Musa
Ayyub|b|Arab|Hebrew|Islamic||Prophet Job, known for patience
Imran|b|Arab|Arabic|Islamic||Surah Al Imran, the family of Imran
Luqman|b|Arab|Arabic|Islamic||wise man of Surah Luqman
Bilal|b|Arab|Arabic|Islamic|moisture, freshness|the first muezzin of Islam
Khalid|b|Arab|Arabic||eternal|
Tariq|b|Arab|Arabic|Islamic|morning star|Surah At-Tariq
Zayd|b|Arab|Arabic|Islamic|growth|the only companion named in the Quran
Hamza|b|Arab|Arabic|Islamic|strong, steadfast|uncle of the Prophet
Rayyan|b|Arab|Arabic|Islamic|well-watered|gate of Paradise for those who fast
Salman|b|Persian|Arabic|Islamic|safe|Salman the Persian, companion of the Prophet
Karim|b|Arab|Arabic|Islamic|generous|one of the 99 names of God
Rashid|b|Arab|Arabic|Islamic|rightly guided|
Faisal|b|Arab|Arabic||decisive judge|
Nasser|b|Arab|Arabic||helper, victorious|
Samir|b|Arab|Arabic||companion in evening talk|
Amir|b|Arab|Arabic||prince, commander|
Malik|b|Arab|Arabic|Islamic|king|
Jamal|b|Arab|Arabic||beauty|
Zain|b|Arab|Arabic||beauty, grace|
Adam|b|Hebrew|Hebrew|Islamic,Jewish,Christian|earth; man|the first human
Maryam|g|Arab|Hebrew|Islamic|beloved|mother of Isa; Surah Maryam
Fatima|g|Arab|Arabic|Islamic|one who abstains|daughter of the Prophet
Aisha|g|Arab|Arabic|Islamic|living, alive|wife of the Prophet
Khadija|g|Arab|Arabic|Islamic|early-born child|first wife of the Prophet, first Muslim
Zainab|g|Arab|Arabic|Islamic|fragrant flower|daughter of the Prophet
Ruqayya|g|Arab|Arabic|Islamic||daughter of the Prophet
Hawa|g|Arab|Hebrew|Islamic|life|Eve, the first woman
Asiya|g|Arab|Arabic|Islamic||wife of Pharaoh, honored for her faith
Hajar|g|Arab|Hebrew|Islamic||mother of Ismail; ran between Safa and Marwa
Amina|g|Arab|Arabic|Islamic|trustworthy|mother of the Prophet
Halima|g|Arab|Arabic|Islamic|gentle, patient|foster mother of the Prophet
Sumayya|g|Arab|Arabic|Islamic||the first martyr of Islam
Safiya|g|Arab|Arabic|Islamic|pure|
Layla|g|Arab|Arabic||night|Layla and Majnun
Noor|e|Arab|Arabic|Islamic|light|Surah An-Nur
Huda|g|Arab|Arabic|Islamic|guidance|
Iman|g|Arab|Arabic|Islamic|faith|
Jannah|g|Arab|Arabic|Islamic|paradise, garden|
Amal|g|Arab|Arabic||hope|
Salma|g|Arab|Arabic||peaceful, safe|
Rania|g|Arab|Arabic||queenly|
Samira|g|Arab|Arabic||companion in evening talk|
Hana|g|Arab|Arabic||happiness|
Malak|g|Arab|Arabic|Islamic|angel|
Inaya|g|Arab|Arabic||care, concern|
Zahra|g|Arab|Arabic|Islamic|radiant, blossoming|a title of Fatima
Yasmin|g|Persian|Persian||jasmine|
Cyrus|b|Persian|Persian|Zoroastrian|sun|Cyrus the Great
Darius|b|Persian|Persian|Zoroastrian|holder of the good|Darius the Great
Roxana|g|Persian|Persian||dawn, little star|
Shirin|g|Persian|Persian||sweet|Khosrow and Shirin
Laleh|g|Persian|Persian||tulip|
Navid|b|Persian|Persian||good news|
Arash|b|Persian|Persian|Zoroastrian||legendary archer who set Iran's border
Rostam|b|Persian|Persian|Zoroastrian||hero of the Shahnameh
Jamshid|b|Persian|Persian|Zoroastrian||legendary king of the Shahnameh
Anahita|g|Persian|Persian|Zoroastrian|immaculate|goddess of the waters
Soraya|g|Persian|Persian||the Pleiades|
Parisa|g|Persian|Persian||like a fairy|
Kian|b|Persian|Persian||king, royal|
Azadeh|g|Persian|Persian||free, noble|
Abraham|b|Hebrew|Hebrew|Jewish,Christian|father of many|patriarch of the Bible
Isaac|b|Hebrew|Hebrew|Jewish,Christian|he will laugh|son of Abraham and Sarah
Jacob|b|Hebrew|Hebrew|Jewish,Christian|held by the heel|father of the twelve tribes
Joseph|b|Hebrew|Hebrew|Jewish,Christian|God will increase|the coat of many colors
Moses|b|Hebrew|Hebrew|Jewish,Christian|drawn out|led the Israelites out of Egypt
Aaron|b|Hebrew|Hebrew|Jewish,Christian||first high priest, brother of Moses
David|b|Hebrew|Hebrew|Jewish,Christian|beloved|shepherd who defeated Goliath, king of Israel
Solomon|b|Hebrew|Hebrew|Jewish,Christian|peace|king famed for wisdom
Samuel|b|Hebrew|Hebrew|Jewish,Christian|God has heard|prophet who anointed David
Elijah|b|Hebrew|Hebrew|Jewish,Christian|my God is Yahweh|prophet taken up in a chariot of fire
Isaiah|b|Hebrew|Hebrew|Jewish,Christian|salvation of the Lord|major prophet
Daniel|b|Hebrew|Hebrew|Jewish,Christian|God is my judge|survived the lions' den
Ezra|b|Hebrew|Hebrew|Jewish,Christian|help|scribe who led the return to Jerusalem
Noah|b|Hebrew|Hebrew|Jewish,Christian|rest|built the ark
Benjamin|b|Hebrew|Hebrew|Jewish,Christian|son of the right hand|youngest son of Jacob
Caleb|b|Hebrew|Hebrew|Jewish,Christian|wholehearted|faithful spy sent into Canaan
Levi|b|Hebrew|Hebrew|Jewish,Christian|joined|son of Jacob, ancestor of the priests
Gideon|b|Hebrew|Hebrew|Jewish,Christian|hewer|judge who won with 300 men
Jonah|b|Hebrew|Hebrew|Jewish,Christian|dove|swallowed by a great fish
Micah|b|Hebrew|Hebrew|Jewish,Christian|who is like God?|prophet
Asher|b|Hebrew|Hebrew|Jewish,Christian|happy, blessed|son of Jacob
Eli|b|Hebrew|Hebrew|Jewish,Christian|ascended|priest who raised Samuel
Ezekiel|b|Hebrew|Hebrew|Jewish,Christian|God strengthens|prophet of the valley of dry bones
Nathan|b|Hebrew|Hebrew|Jewish,Christian|he gave|prophet in David's court
Reuben|b|Hebrew|Hebrew|Jewish,Christian|behold, a son|eldest son of Jacob
Judah|b|Hebrew|Hebrew|Jewish,Christian|praised|son of Jacob
Joshua|b|Hebrew|Hebrew|Jewish,Christian|God is salvation|led Israel into the Promised Land
Seth|b|Hebrew|Hebrew|Jewish,Christian|appointed|third son of Adam and Eve
Jesse|b|Hebrew|Hebrew|Jewish,Christian|gift|father of King David
Tobias|b|Hebrew|Hebrew|Christian|God is good|Book of Tobit
Raphael|b|Hebrew|Hebrew|Jewish,Christian|God heals|archangel
Gabriel|b|Hebrew|Hebrew|Jewish,Christian,Islamic|God is my strength|archangel (Jibril in Islam)
Michael|b|Hebrew|Hebrew|Jewish,Christian|who is like God?|archangel
Sarah|g|Hebrew|Hebrew|Jewish,Christian,Islamic|princess|wife of Abraham
Rebecca|g|Hebrew|Hebrew|Jewish,Christian|captivating|wife of Isaac
Rachel|g|Hebrew|Hebrew|Jewish,Christian|ewe|beloved wife of Jacob
Leah|g|Hebrew|Hebrew|Jewish,Christian|weary; delicate|wife of Jacob
Miriam|g|Hebrew|Hebrew|Jewish,Christian||prophetess, sister of Moses
Eve|g|Hebrew|Hebrew|Jewish,Christian|life|the first woman
Hannah|g|Hebrew|Hebrew|Jewish,Christian|grace, favor|mother of Samuel
Ruth|g|Hebrew|Hebrew|Jewish,Christian|friend|loyal daughter-in-law of Naomi
Naomi|g|Hebrew|Hebrew|Jewish,Christian|pleasantness|mother-in-law of Ruth
Esther|g|Persian|Persian|Jewish,Christian|star|queen who saved her people; Purim
Deborah|g|Hebrew|Hebrew|Jewish,Christian|bee|prophetess and judge of Israel
Abigail|g|Hebrew|Hebrew|Jewish,Christian|my father's joy|wise wife of King David
Judith|g|Hebrew|Hebrew|Jewish,Christian|woman of Judea|heroine of the Book of Judith
Dinah|g|Hebrew|Hebrew|Jewish,Christian|judged|daughter of Jacob
Tamar|g|Hebrew|Hebrew|Jewish,Christian|date palm|
Zipporah|g|Hebrew|Hebrew|Jewish,Christian|bird|wife of Moses
Shiloh|e|Hebrew|Hebrew|Jewish,Christian|peaceful|
Eliana|g|Hebrew|Hebrew|Jewish|my God has answered|
Adina|g|Hebrew|Hebrew|Jewish|gentle|
Talia|g|Hebrew|Hebrew|Jewish|dew from God|
Noa|g|Hebrew|Hebrew|Jewish|movement|daughter of Zelophehad
Yael|g|Hebrew|Hebrew|Jewish|mountain goat|heroine in the Book of Judges
Shira|g|Hebrew|Hebrew|Jewish|song|
Ariel|e|Hebrew|Hebrew|Jewish|lion of God|
Eitan|b|Hebrew|Hebrew|Jewish|strong, firm|
Lior|e|Hebrew|Hebrew|Jewish|my light|
Avi|b|Hebrew|Hebrew|Jewish|my father|
Tova|g|Hebrew|Hebrew|Jewish|good|
Zev|b|Hebrew|Hebrew|Jewish|wolf|
Aviva|g|Hebrew|Hebrew|Jewish|springtime|
Ori|b|Hebrew|Hebrew|Jewish|my light|
Matthew|b|Hebrew|Hebrew|Christian|gift of God|Apostle and Gospel writer
John|b|Hebrew|Hebrew|Christian|God is gracious|Apostle and Gospel writer
Mary|g|Hebrew|Hebrew|Christian||mother of Jesus
Elizabeth|g|Hebrew|Hebrew|Christian|God is my oath|mother of John the Baptist
Joanna|g|Hebrew|Hebrew|Christian|God is gracious|follower of Jesus
Anna|g|Hebrew|Hebrew|Christian|grace|prophetess at the Temple
Martha|g|Aramaic|Aramaic|Christian|lady|sister of Lazarus
Thomas|b|Aramaic|Aramaic|Christian|twin|the Apostle Thomas
Bartholomew|b|Aramaic|Aramaic|Christian|son of Talmai|one of the Twelve Apostles
Barnabas|b|Aramaic|Aramaic|Christian|son of encouragement|missionary with Paul
Magdalene|g|Hebrew|Hebrew|Christian|from Magdala|Mary Magdalene
James|b|Hebrew|Hebrew|Christian|supplanter|two of the Twelve Apostles
Paul|b|Latin|Latin|Christian|small|the Apostle Paul
Mark|b|Latin|Latin|Christian|dedicated to Mars|author of the Gospel of Mark
Priscilla|g|Latin|Latin|Christian|ancient|early Christian teacher
Christopher|b|Greek|Greek|Christian|Christ-bearer|patron saint of travelers
Christian|b|Latin|Latin|Christian|follower of Christ|
Grace|g|English|English|Christian|grace|virtue name
Faith|g|English|English|Christian|faith|virtue name
Hope|g|English|English|Christian|hope|virtue name
Benedict|b|Latin|Latin|Christian|blessed|Saint Benedict
Francis|b|Latin|Latin|Christian|Frenchman|Saint Francis of Assisi
Clare|g|Latin|Latin|Christian|bright, clear|Saint Clare of Assisi
Augustine|b|Latin|Latin|Christian|venerable|Saint Augustine
Patrick|b|Irish|Latin|Christian|nobleman|patron saint of Ireland
Teresa|g|Spanish|Greek|Christian|harvester|Saint Teresa of Ávila
Aurelia|g|Latin|Latin||golden|
Julius|b|Latin|Latin||youthful|Julius Caesar
Maximus|b|Latin|Latin||greatest|
Felix|b|Latin|Latin||lucky, happy|
Luna|g|Latin|Latin||moon|Roman goddess of the moon
Victoria|g|Latin|Latin||victory|
Octavia|g|Latin|Latin||eighth|
Lucius|b|Latin|Latin||light|
Atticus|b|Latin|Latin||from Attica|
Aurora|g|Latin|Latin||dawn|Roman goddess of the dawn
Juno|g|Latin|Latin||queen of the Roman gods|
Giovanni|b|Italian|Italian|Christian|God is gracious|
Lorenzo|b|Italian|Italian||from Laurentum|
Matteo|b|Italian|Italian|Christian|gift of God|
Giulia|g|Italian|Italian||youthful|
Francesca|g|Italian|Italian|Christian|free|
Chiara|g|Italian|Italian|Christian|bright, clear|
Alessandro|b|Italian|Italian||defender of the people|
Bianca|g|Italian|Italian||white|
Leonardo|b|Italian|Italian||brave lion|Leonardo da Vinci
Gianna|g|Italian|Italian|Christian|God is gracious|
Mateo|b|Spanish|Spanish|Christian|gift of God|
Santiago|b|Spanish|Spanish|Christian|Saint James|the Camino de Santiago
Diego|b|Spanish|Spanish|Christian|supplanter|
Alejandro|b|Spanish|Spanish||defender of the people|
Lucía|g|Spanish|Spanish|Christian|light|Saint Lucy
Valentina|g|Spanish|Spanish||strong, healthy|
Camila|g|Spanish|Spanish||helper at sacred rites|
Guadalupe|g|Spanish|Spanish|Christian||Our Lady of Guadalupe
Dolores|g|Spanish|Spanish|Christian|sorrows|Our Lady of Sorrows
Marisol|g|Spanish|Spanish|Christian|sea and sun|
Paloma|g|Spanish|Spanish|Christian|dove|
Ximena|g|Spanish|Spanish||listener|
Inés|g|Spanish|Spanish|Christian|pure|Saint Agnes
Javier|b|Spanish|Spanish|Christian|new house|Saint Francis Xavier
Joaquín|b|Spanish|Spanish|Christian|raised by God|father of Mary
Jesús|b|Spanish|Spanish|Christian|God saves|
Amélie|g|French|French||hardworking|
Juliette|g|French|French||youthful|
Margot|g|French|French||pearl|
Lucien|b|French|French||light|
Étienne|b|French|French|Christian|crown|
Louis|b|French|French||famous warrior|
Céline|g|French|French||heavenly|
Noël|e|French|French|Christian|Christmas|
René|b|French|French|Christian|reborn|
Aoife|g|Irish|Irish|Celtic myth|beauty, radiance|warrior woman of Irish legend
Saoirse|g|Irish|Irish||freedom|
Niamh|g|Irish|Irish|Celtic myth|bright, radiant|queen of Tír na nÓg
Siobhan|g|Irish|Irish|Christian|God is gracious|
Ciara|g|Irish|Irish|Christian|dark|Saint Ciara
Róisín|g|Irish|Irish||little rose|
Aisling|g|Irish|Irish||dream, vision|
Orla|g|Irish|Irish||golden princess|
Cillian|b|Irish|Irish|Christian|little church|
Oisín|b|Irish|Irish|Celtic myth|little deer|poet-hero of the Fenian Cycle
Cian|b|Irish|Irish|Celtic myth|ancient|father of Lugh
Darragh|b|Irish|Irish||oak tree|
Fionn|b|Irish|Irish|Celtic myth|fair, bright|Fionn mac Cumhaill
Liam|b|Irish|Irish||strong-willed protector|
Ronan|b|Irish|Irish|Christian|little seal|
Brigid|g|Irish|Irish|Christian,Celtic myth|exalted one|goddess and patron saint of Ireland
Eoin|b|Irish|Irish|Christian|God is gracious|
Isla|g|Scottish|Scottish Gaelic||island|
Callum|b|Scottish|Scottish Gaelic|Christian|dove|Saint Columba
Fiona|g|Scottish|Scottish Gaelic||white, fair|
Rhys|b|Welsh|Welsh||ardor|
Dylan|b|Welsh|Welsh|Celtic myth|son of the sea|sea god of Welsh legend
Carys|g|Welsh|Welsh||love|
Seren|g|Welsh|Welsh||star|
Owen|b|Welsh|Welsh||noble, well-born|
Edward|b|English|Old English||rich guardian|
Alfred|b|English|Old English||elf counsel|Alfred the Great
Audrey|g|English|Old English||noble strength|
Edith|g|English|Old English||rich in war|
Hazel|g|English|English||hazel tree|
Willow|g|English|English||willow tree|
Wren|e|English|English||small songbird|
Harper|e|English|English||harp player|
Wilhelm|b|German|German||will + helmet|
Friedrich|b|German|German||peaceful ruler|
Greta|g|German|German||pearl|
Heidi|g|German|German||noble|
Emma|g|German|German||whole, universal|
Matilda|g|German|German||mighty in battle|
Otto|b|German|German||wealth|
Ada|g|German|German||noble|
Ludwig|b|German|German||famous warrior|
Karl|b|German|German||free man|
Freya|g|Norse|Old Norse|Norse myth|lady|goddess of love
Thor|b|Norse|Old Norse|Norse myth|thunder|god of thunder
Odin|b|Norse|Old Norse|Norse myth|frenzy, inspiration|chief of the gods
Astrid|g|Norse|Old Norse||divinely beautiful|
Ingrid|g|Norse|Old Norse|Norse myth|beautiful (like the god Ing)|
Sigrid|g|Norse|Old Norse||beautiful victory|
Leif|b|Norse|Old Norse||heir|Leif Erikson
Bjorn|b|Norse|Old Norse||bear|
Erik|b|Norse|Old Norse||eternal ruler|
Ragnar|b|Norse|Old Norse||warrior of the gods|
Liv|g|Norse|Old Norse||life|
Solveig|g|Norse|Old Norse||strength of the sun|
Baldur|b|Norse|Old Norse|Norse myth||god of light
Idun|g|Norse|Old Norse|Norse myth||goddess of youth and golden apples
Saga|g|Norse|Old Norse|Norse myth|seeing one|goddess of stories
Embla|g|Norse|Old Norse|Norse myth||the first woman
Tyr|b|Norse|Old Norse|Norse myth||god of war and justice
Haruto|b|Japanese|Japanese||sun, soaring|
Ren|e|Japanese|Japanese|Buddhist|lotus|
Sora|e|Japanese|Japanese||sky|
Hiroshi|b|Japanese|Japanese||generous|
Takumi|b|Japanese|Japanese||artisan|
Riku|b|Japanese|Japanese||land|
Yuki|e|Japanese|Japanese||snow; happiness|
Sakura|g|Japanese|Japanese||cherry blossom|
Hana|g|Japanese|Japanese||flower|
Aiko|g|Japanese|Japanese||child of love|
Akira|e|Japanese|Japanese||bright, clear|
Hinata|e|Japanese|Japanese||sunny place|
Kaito|b|Japanese|Japanese||ocean, soaring|
Wei|b|Chinese|Mandarin||great|
Ming|e|Chinese|Mandarin||bright|
Mei|g|Chinese|Mandarin||beautiful|
Lan|g|Chinese|Mandarin||orchid|
Jing|g|Chinese|Mandarin||quiet, calm|
Jun|b|Chinese|Mandarin||handsome, talented|
Lian|g|Chinese|Mandarin|Buddhist|lotus|
Seo-yeon|g|Korean|Korean||auspicious, beautiful|
Min-jun|b|Korean|Korean||quick, handsome|
Ayodele|e|African|Yoruba||joy has come home|
Femi|e|African|Yoruba||love me|
Folami|g|African|Yoruba||respect and honor me|
Adebayo|b|African|Yoruba||the crown meets joy|
Oluwaseun|e|African|Yoruba|Christian,Islamic|we thank God|
Chiamaka|g|African|Igbo|Christian|God is beautiful|
Chinonso|e|African|Igbo|Christian|God is near|
Chidi|b|African|Igbo|Christian|God exists|
Amara|g|African|Igbo||grace|
Nkechi|g|African|Igbo|Christian|God's own|
Obinna|b|African|Igbo||father's heart|
Adaeze|g|African|Igbo||princess|
Kelechi|e|African|Igbo|Christian|praise God|
Imani|g|African|Swahili||faith|
Baraka|b|African|Swahili||blessing|
Zuri|g|African|Swahili||beautiful|
Amani|e|African|Swahili||peace|
Jabari|b|African|Swahili||brave|
Neema|g|African|Swahili||grace|
Rehema|g|African|Swahili||compassion|
Jelani|b|African|Swahili||mighty|
Kofi|b|African|Akan||born on Friday|
Kwame|b|African|Akan||born on Saturday|
Ama|g|African|Akan||born on Saturday|
Akosua|g|African|Akan||born on Sunday|
Abena|g|African|Akan||born on Tuesday|
Selam|g|African|Amharic|Christian|peace|
Tesfaye|b|African|Amharic|Christian|my hope|
Makeda|g|African|Amharic|Christian||the Queen of Sheba in Ethiopian tradition
Emir|b|Turkish|Turkish||commander|
Deniz|e|Turkish|Turkish||sea|
Elif|g|Turkish|Turkish||slender; first letter of the alphabet|
Aylin|g|Turkish|Turkish||moon halo|
Kaan|b|Turkish|Turkish||ruler|
Defne|g|Turkish|Turkish||laurel|
Mert|b|Turkish|Turkish||brave|
Yağmur|g|Turkish|Turkish||rain|
Mila|g|Slavic|Slavic||gracious, dear|
Vera|g|Slavic|Slavic|Christian|faith|
Nadia|g|Slavic|Slavic|Christian|hope|
Ivan|b|Slavic|Slavic|Christian|God is gracious|
Natasha|g|Slavic|Slavic|Christian|born on Christmas|
Milan|b|Slavic|Slavic||gracious, dear|
Bogdan|b|Slavic|Slavic|Christian|given by God|
Zora|g|Slavic|Slavic||dawn|
Kai|e|Hawaiian|Hawaiian||sea|
Leilani|g|Hawaiian|Hawaiian||heavenly flowers|
Kalani|e|Hawaiian|Hawaiian||the heavens|
Keanu|b|Hawaiian|Hawaiian||the cool breeze|
Malia|g|Hawaiian|Hawaiian|Christian||Hawaiian form of Mary
Koa|b|Hawaiian|Hawaiian||warrior; the koa tree|
Tenzin|e|Tibetan|Tibetan|Buddhist|upholder of the teachings|the Dalai Lama's name
Pema|e|Tibetan|Tibetan|Buddhist|lotus|
Dorje|b|Tibetan|Tibetan|Buddhist|thunderbolt|
Thandiwe|g|Zulu|Zulu||beloved|
Sipho|b|Zulu|Zulu||gift|
Nomvula|g|Zulu|Zulu||mother of rain; born in the rain|
Themba|b|Zulu|Zulu||hope|
Lwazi|b|Zulu|Zulu||knowledge|
Ayanda|e|Zulu|Zulu||they are increasing; the family grows|
Andile|e|Zulu|Zulu||they have increased|
Bongani|b|Zulu|Zulu||be thankful|
Lindiwe|g|Zulu|Zulu||the awaited one|
Zanele|g|Zulu|Zulu||they are enough|
Nandi|g|Zulu|Zulu||sweet|mother of the Zulu king Shaka
Mandla|b|Zulu|Zulu||strength, power|
Sizwe|b|Zulu|Zulu||nation|
Melokuhle|g|Zulu|Zulu||good conduct|among South Africa's most popular girls' names
Enzokuhle|e|Zulu|Zulu||good deeds|
Nkazimulo|b|Zulu|Zulu||glory|
Siyabonga|b|Zulu|Zulu||we thank you|
Thulani|b|Zulu|Zulu||be quiet, be calm|
Nokuthula|g|Zulu|Zulu||peace; mother of peace|
Lubanzi|b|Xhosa|Xhosa||breadth, wide open|among South Africa's most popular boys' names
Lulama|e|Xhosa|Xhosa||be gentle, be kind|
Unathi|e|Xhosa|Xhosa||God is with us|
Thando|e|Xhosa|Xhosa||love|
Lathitha|g|Xhosa|Xhosa||light, it is bright|
Thabo|b|Sotho|Sotho||joy, happiness|
Lerato|g|Sotho|Sotho||love|
Palesa|g|Sotho|Sotho||flower|
Mpho|e|Sotho|Sotho||gift|
Naledi|g|Sotho|Sotho||star|
Lesedi|e|Sotho|Sotho||light|
Lethabo|e|Sotho|Sotho||joy|South Africa's most popular boys' name in recent years
Karabo|e|Sotho|Sotho||answer|
Tumelo|e|Sotho|Sotho||faith|
Kagiso|e|Tswana|Tswana||peace|
Boitumelo|e|Tswana|Tswana||joy|
Refilwe|g|Tswana|Tswana||we have been given|
Tshepo|b|Tswana|Tswana||hope, trust|
Kgosi|b|Tswana|Tswana||king, chief|
Dineo|g|Tswana|Tswana||gifts|
Amani|e|Swahili|Swahili||peace|
Imani|e|Swahili|Swahili||faith|
Baraka|b|Swahili|Swahili||blessing|
Neema|g|Swahili|Swahili||grace|
Zawadi|g|Swahili|Swahili||gift|
Rehema|g|Swahili|Swahili||mercy, compassion|
Jabari|b|Swahili|Swahili||brave, fearless|
Juma|b|Swahili|Swahili||born on Friday|
Furaha|g|Swahili|Swahili||joy|
Tumaini|e|Swahili|Swahili||hope|
Upendo|g|Swahili|Swahili||love|
Zuri|g|Swahili|Swahili||beautiful|
Shujaa|b|Swahili|Swahili||hero|
Jelani|b|Swahili|Swahili||mighty|
Nia|g|Swahili|Swahili||purpose|
Kwame|b|Akan|Akan||born on Saturday|Akan day name
Kofi|b|Akan|Akan||born on Friday|Akan day name
Kwabena|b|Akan|Akan||born on Tuesday|Akan day name
Kwaku|b|Akan|Akan||born on Wednesday|Akan day name
Yaw|b|Akan|Akan||born on Thursday|Akan day name
Kwasi|b|Akan|Akan||born on Sunday|Akan day name
Kojo|b|Akan|Akan||born on Monday|Akan day name
Ama|g|Akan|Akan||born on Saturday|Akan day name
Afua|g|Akan|Akan||born on Friday|Akan day name
Abena|g|Akan|Akan||born on Tuesday|Akan day name
Akua|g|Akan|Akan||born on Wednesday|Akan day name
Yaa|g|Akan|Akan||born on Thursday|Akan day name
Akosua|g|Akan|Akan||born on Sunday|Akan day name
Adwoa|g|Akan|Akan||born on Monday|Akan day name
Hodan|g|Somali|Somali||wealthy, abundant|
Ayaan|g|Somali|Somali||lucky, blessed|
Ubah|g|Somali|Somali||flower|
Nimco|g|Somali|Somali||blessing|
Hamdi|g|Somali|Somali||praise|
Ifrah|g|Somali|Somali||joy|
Liban|b|Somali|Somali||fortunate, successful|
Warsame|b|Somali|Somali||bringer of good news|
Mahad|b|Somali|Somali||thanks|
Selam|g|Ethiopian|Amharic||peace|
Tesfaye|b|Ethiopian|Amharic||my hope|
Haile|b|Ethiopian|Amharic||power, might|
Tigist|g|Ethiopian|Amharic||patience|
Almaz|g|Ethiopian|Amharic||diamond|
Kidist|g|Ethiopian|Amharic||holy|
Meseret|g|Ethiopian|Amharic||foundation|
Abebe|b|Ethiopian|Amharic||he has blossomed|
Selamawit|g|Ethiopian|Amharic||peaceful|
Gurpreet|e|Punjabi|Punjabi|Sikh|love of the Guru|
Harpreet|e|Punjabi|Punjabi|Sikh|love of God|
Manpreet|e|Punjabi|Punjabi|Sikh|love from the heart|
Jaspreet|e|Punjabi|Punjabi|Sikh|love of praise|
Simran|e|Punjabi|Punjabi|Sikh|remembrance (of God)|
Amrit|e|Punjabi|Punjabi|Sikh|nectar of immortality|
Navjot|e|Punjabi|Punjabi|Sikh|new light|
Gurdeep|b|Punjabi|Punjabi|Sikh|lamp of the Guru|
Kirandeep|g|Punjabi|Punjabi|Sikh|ray of the lamp|
Jasleen|g|Punjabi|Punjabi|Sikh|absorbed in praise|
Ekam|b|Punjabi|Punjabi|Sikh|one; oneness (of God)|
Sana|g|Urdu|Urdu|Islamic|praise, radiance|
Mahnoor|g|Urdu|Urdu|Islamic|moonlight|
Hira|g|Urdu|Urdu|Islamic|diamond|
Anam|g|Urdu|Urdu|Islamic|blessing|
Areeba|g|Urdu|Urdu|Islamic|wise, witty|
Kashif|b|Urdu|Urdu|Islamic|discoverer|
Faisal|b|Urdu|Urdu|Islamic|decisive, judge|
Shahzeb|b|Urdu|Urdu|Islamic|ornament of the king|
Gulalai|g|Pashtun|Pashto|Islamic|flower-like|
Zarmina|g|Pashtun|Pashto|Islamic|golden|
Somchai|b|Thai|Thai|Buddhist|worthy man|
Malee|g|Thai|Thai|Buddhist|jasmine flower|
Siriporn|g|Thai|Thai|Buddhist|glorious blessing|
Kanya|g|Thai|Thai|Buddhist|maiden|
Anong|g|Thai|Thai|Buddhist|beautiful woman|
Ratana|g|Thai|Thai|Buddhist|jewel|
Niran|b|Thai|Thai|Buddhist|eternal|
Prasert|b|Thai|Thai|Buddhist|excellent|
Kittisak|b|Thai|Thai|Buddhist|honor and power|
Sunee|g|Thai|Thai|Buddhist|good, kind|
Tenzin|e|Tibetan|Tibetan|Buddhist|upholder of the teachings|
Pema|e|Tibetan|Tibetan|Buddhist|lotus|
Dorje|b|Tibetan|Tibetan|Buddhist|thunderbolt, indestructible|
Sonam|e|Tibetan|Tibetan|Buddhist|merit, fortunate|
Dolma|g|Tibetan|Tibetan|Buddhist|Tara, the savior goddess|
Lhamo|g|Tibetan|Tibetan|Buddhist|goddess|
Nyima|e|Tibetan|Tibetan|Buddhist|sun; born on Sunday|
Dawa|e|Tibetan|Tibetan|Buddhist|moon; born on Monday|
Tashi|e|Tibetan|Tibetan|Buddhist|auspicious, good fortune|
Norbu|b|Tibetan|Tibetan|Buddhist|jewel|
Bishal|b|Nepali|Nepali|Hindu|vast, great|
Aayush|b|Nepali|Nepali|Hindu|long life|
Srijana|g|Nepali|Nepali|Hindu|creation|
Pasang|e|Nepali|Sherpa|Buddhist|born on Friday|Sherpa day name
Mingma|e|Nepali|Sherpa|Buddhist|born on Tuesday|Sherpa day name
Aung|b|Burmese|Burmese|Buddhist|success, victory|
Thida|g|Burmese|Burmese|Buddhist|truth|
Zaw|b|Burmese|Burmese|Buddhist|famous|
Khin|g|Burmese|Burmese|Buddhist|friendly, lovable|
Sopheap|g|Khmer|Khmer|Buddhist|gentle, polite|
Sokha|e|Khmer|Khmer|Buddhist|health, happiness|
Dara|b|Khmer|Khmer|Buddhist|star|
Bopha|g|Khmer|Khmer|Buddhist|flower|
Chantrea|g|Khmer|Khmer|Buddhist|moonlight|
Alofa|g|Samoan|Samoan||love|
Fetu|e|Samoan|Samoan||star|
Manu|b|Samoan|Samoan||bird|
Sione|b|Tongan|Tongan|Christian|John|
Mele|g|Tongan|Tongan|Christian|Mary|
Salote|g|Tongan|Tongan|Christian|Charlotte|name of Queen Sālote Tupou III
Malakai|b|Tongan|Tongan|Christian|Malachi|
Mere|g|Fijian|Fijian|Christian|Mary|
Vilisoni|b|Fijian|Fijian|Christian|Wilson|
Arthit|b|Thai|Thai|Buddhist|sun|
Suriya|b|Thai|Thai|Buddhist|sun|
Chanthira|g|Thai|Thai|Buddhist|moon|
Duangjai|g|Thai|Thai|Buddhist|heart; beloved|
Kanokwan|g|Thai|Thai|Buddhist|golden complexion|
Kamon|e|Thai|Thai|Buddhist|lotus; heart|
Kittipong|b|Thai|Thai|Buddhist|lineage of honor|
Nattapong|b|Thai|Thai|Buddhist|lineage of the wise|
Sakda|b|Thai|Thai|Buddhist|power, might|
Somsak|b|Thai|Thai|Buddhist|worthy of honor|
Somporn|e|Thai|Thai|Buddhist|worthy of blessings|
Supachai|b|Thai|Thai|Buddhist|auspicious victory|
Thanawat|b|Thai|Thai|Buddhist|growing wealth|
Wichai|b|Thai|Thai|Buddhist|victory|
Chai|b|Thai|Thai|Buddhist|victory|
Wanida|g|Thai|Thai|Buddhist|woman, lady|
Naree|g|Thai|Thai|Buddhist|woman|
Pornthip|g|Thai|Thai|Buddhist|divine blessing|
Rungnapa|g|Thai|Thai|Buddhist|rainbow in the sky|
Benjamas|g|Thai|Thai|Buddhist|chrysanthemum|
Saowalak|g|Thai|Thai|Buddhist|of fine features|
Ploy|g|Thai|Thai|Buddhist|gem|
Fah|g|Thai|Thai|Buddhist|sky|
Dao|g|Thai|Thai|Buddhist|star|
Kulap|g|Thai|Thai|Buddhist|rose|
Aye|e|Burmese|Burmese|Buddhist|calm, cool|
Hla|e|Burmese|Burmese|Buddhist|beautiful|
Mya|g|Burmese|Burmese|Buddhist|emerald|
Myint|b|Burmese|Burmese|Buddhist|high, lofty|
Kyaw|b|Burmese|Burmese|Buddhist|famous, renowned|
Win|b|Burmese|Burmese|Buddhist|bright, radiant|
Htet|b|Burmese|Burmese|Buddhist|superior, higher|
Min|b|Burmese|Burmese|Buddhist|king|
Thant|b|Burmese|Burmese|Buddhist|clean, pure|U Thant, third UN Secretary-General
Phyu|e|Burmese|Burmese|Buddhist|white|
Khaing|e|Burmese|Burmese|Buddhist|firm, strong|
Thiri|g|Burmese|Burmese|Buddhist|glory, splendor|
Moe|e|Burmese|Burmese|Buddhist|rain; sky|
Nyein|e|Burmese|Burmese|Buddhist|calm, peaceful|
Kyi|e|Burmese|Burmese|Buddhist|clear, bright|
Naing|b|Burmese|Burmese|Buddhist|to win, victorious|
Tun|b|Burmese|Burmese|Buddhist|bright, shining|
Shwe|e|Burmese|Burmese|Buddhist|gold|
Ngwe|e|Burmese|Burmese|Buddhist|silver|
Yadanar|g|Burmese|Burmese|Buddhist|jewel, treasure|
Sandar|g|Burmese|Burmese|Buddhist|moon|
Vanna|e|Khmer|Khmer|Buddhist|golden-colored|
Kosal|b|Khmer|Khmer|Buddhist|merit, good deeds|
Rithy|b|Khmer|Khmer|Buddhist|power|
Visal|b|Khmer|Khmer|Buddhist|great, vast|
Pich|e|Khmer|Khmer|Buddhist|diamond|
Srey|g|Khmer|Khmer|Buddhist|woman, girl|
Mealea|g|Khmer|Khmer|Buddhist|garland|
Phalla|e|Khmer|Khmer|Buddhist|fruit|
Sovann|e|Khmer|Khmer|Buddhist|gold|
Socheata|g|Khmer|Khmer|Buddhist|well-born|
Kunthea|g|Khmer|Khmer|Buddhist|fragrance|
Leakhena|g|Khmer|Khmer|Buddhist|of fine features|
Veasna|b|Khmer|Khmer|Buddhist|destiny|
Seyha|b|Khmer|Khmer|Buddhist|lion|
Samnang|b|Khmer|Khmer|Buddhist|lucky|
Thida|g|Khmer|Khmer|Buddhist|daughter|
Ratanak|b|Khmer|Khmer|Buddhist|jewel|
Sophal|b|Khmer|Khmer|Buddhist|fruitful, prosperous|
Sina|g|Samoan|Samoan||white|heroine of the legend of Sina and the eel, which became the first coconut
Masina|g|Samoan|Samoan||moon|
Lagi|e|Samoan|Samoan||sky, heaven|
Moana|e|Samoan|Samoan||ocean, deep sea|
Malie|g|Samoan|Samoan||pleasant, sweet|
Mana|e|Samoan|Samoan||power, prestige|
Tama|b|Samoan|Samoan||boy, child|
Tasi|e|Samoan|Samoan||one|
Tavita|b|Samoan|Samoan|Christian|David|
Losa|g|Samoan|Samoan|Christian|Rose|
Ioane|b|Samoan|Samoan|Christian|John|
Iosefa|b|Samoan|Samoan|Christian|Joseph|
Sefo|b|Samoan|Samoan|Christian|Joe, Joseph|
Pita|b|Samoan|Samoan|Christian|Peter|
Mikaele|b|Samoan|Samoan|Christian|Michael|
Peniamina|b|Samoan|Samoan|Christian|Benjamin|
Elisapeta|g|Samoan|Samoan|Christian|Elizabeth|
Mele|g|Samoan|Samoan|Christian|Mary|
Souksavanh|e|Lao|Lao|Buddhist|happiness of heaven|
Souk|e|Lao|Lao|Buddhist|happiness|
Sisouk|e|Lao|Lao|Buddhist|glorious happiness|
Bounmy|e|Lao|Lao|Buddhist|one who has merit|
Sengdao|g|Lao|Lao|Buddhist|starlight|
Phonsavanh|e|Lao|Lao|Buddhist|heavenly blessing|
Kham|e|Lao|Lao|Buddhist|gold|
Bouakham|g|Lao|Lao|Buddhist|golden lotus|
Boua|g|Lao|Lao|Buddhist|lotus|
Khamsing|b|Lao|Lao|Buddhist|golden lion|
Keo|e|Lao|Lao|Buddhist|gem, crystal|
Phet|e|Lao|Lao|Buddhist|diamond|
Chanthala|g|Lao|Lao|Buddhist|moon|
Chanthavong|b|Lao|Lao|Buddhist|lineage of the moon|
Somphone|b|Lao|Lao|Buddhist|worthy of blessings|
Somsack|b|Lao|Lao|Buddhist|worthy of honor|
Mali|g|Lao|Lao|Buddhist|jasmine|
Noy|g|Lao|Lao|Buddhist|little one|
Dao|g|Lao|Lao|Buddhist|star|
Tevita|b|Tongan|Tongan|Christian|David|
Viliami|b|Tongan|Tongan|Christian|William|
Siaosi|b|Tongan|Tongan|Christian|George|
Siosaia|b|Tongan|Tongan|Christian|Josiah|
Semisi|b|Tongan|Tongan|Christian|James|
Sitiveni|b|Tongan|Tongan|Christian|Stephen|
Paula|b|Tongan|Tongan|Christian|Paul|a boys' name in Tonga
Sela|g|Tongan|Tongan|Christian|Sarah|
Lose|g|Tongan|Tongan|Christian|Rose|
Losaline|g|Tongan|Tongan|Christian|Rosaline|
Kalolaine|g|Tongan|Tongan|Christian|Caroline|
Lupe|g|Tongan|Tongan||dove|
Ofa|g|Tongan|Tongan||love|
Mafi|b|Tongan|Tongan||power, strength|
Mahina|g|Tongan|Tongan||moon|
Fetu'u|e|Tongan|Tongan||star|
Kakala|g|Tongan|Tongan||fragrant flowers|
Heilala|g|Tongan|Tongan||the heilala flower, Tonga's national flower|
Moana|e|Tongan|Tongan||ocean, deep sea|
Anuhea|g|Hawaiian|Hawaiian||cool, fragrant breeze|
Haunani|g|Hawaiian|Hawaiian||beautiful dew|
Hina|g|Hawaiian|Hawaiian||goddess of the moon|the moon goddess of Hawaiian legend
Haumea|g|Hawaiian|Hawaiian||goddess of fertility and childbirth|
Ikaika|b|Hawaiian|Hawaiian||strong|
Iokepa|b|Hawaiian|Hawaiian|Christian|Joseph|
Iakopa|b|Hawaiian|Hawaiian|Christian|Jacob|
Iosua|b|Hawaiian|Hawaiian|Christian|Joshua|
Kahale|b|Hawaiian|Hawaiian||the house|
Kailani|g|Hawaiian|Hawaiian||sea and sky|
Kaimana|e|Hawaiian|Hawaiian||diamond|
Kainalu|b|Hawaiian|Hawaiian||the billowing sea|
Kainoa|b|Hawaiian|Hawaiian||the name|
Kaipo|b|Hawaiian|Hawaiian||the sweetheart|
Kalama|e|Hawaiian|Hawaiian||the torch|
Kalei|e|Hawaiian|Hawaiian||the lei; the beloved|
Kaleialoha|g|Hawaiian|Hawaiian||lei of love|
Kaleo|b|Hawaiian|Hawaiian||the voice|
Kaleolani|e|Hawaiian|Hawaiian||heavenly voice|
Kama|b|Hawaiian|Hawaiian||child|
Kamaile|g|Hawaiian|Hawaiian||the maile vine|
Kamaka|b|Hawaiian|Hawaiian||the eye; the face|
Kamalani|g|Hawaiian|Hawaiian||child of heaven|
Kamalei|g|Hawaiian|Hawaiian||beloved child|
Kamehameha|b|Hawaiian|Hawaiian||the lonely one, one set apart|Kamehameha I, who united the Hawaiian Islands
Kamuela|b|Hawaiian|Hawaiian|Christian|Samuel|
Kanaloa|b|Hawaiian|Hawaiian||god of the ocean|
Kanani|g|Hawaiian|Hawaiian||the beauty|
Kaniela|b|Hawaiian|Hawaiian|Christian|Daniel|
Kanoa|b|Hawaiian|Hawaiian||the free one|
Kanoelani|g|Hawaiian|Hawaiian||heavenly mist|
Kapono|b|Hawaiian|Hawaiian||the righteous one|
Kapua|e|Hawaiian|Hawaiian||the flower|
Kaulana|e|Hawaiian|Hawaiian||famous|
Kawai|e|Hawaiian|Hawaiian||the water|
Kawailani|e|Hawaiian|Hawaiian||heavenly water|
Kawehi|e|Hawaiian|Hawaiian||the adornment|
Kawika|b|Hawaiian|Hawaiian|Christian|David|
Kāwika|b|Hawaiian|Hawaiian|Christian|David|
Keahi|e|Hawaiian|Hawaiian||the fire|
Keala|e|Hawaiian|Hawaiian||the path|
Kealani|e|Hawaiian|Hawaiian||the heavenly path|
Kealoha|e|Hawaiian|Hawaiian||the beloved|
Keao|e|Hawaiian|Hawaiian||the dawn|
Kekoa|b|Hawaiian|Hawaiian||the brave one|
Keola|e|Hawaiian|Hawaiian||life|
Keone|b|Hawaiian|Hawaiian||the sand|
Kepano|b|Hawaiian|Hawaiian|Christian|Stephen|
Kiele|g|Hawaiian|Hawaiian||gardenia|
Kimokeo|b|Hawaiian|Hawaiian|Christian|Timothy|
Kimona|b|Hawaiian|Hawaiian|Christian|Simon|
Kolomona|b|Hawaiian|Hawaiian|Christian|Solomon|
Kāne|b|Hawaiian|Hawaiian||man; god of creation and life|
Kēhau|e|Hawaiian|Hawaiian||the dew|
Kēhaulani|g|Hawaiian|Hawaiian||heavenly dew|
Kalā|e|Hawaiian|Hawaiian||the sun|
Kalehua|e|Hawaiian|Hawaiian||the lehua blossom|
Laka|g|Hawaiian|Hawaiian||goddess of hula|
Lanakila|b|Hawaiian|Hawaiian||victory|
Lani|e|Hawaiian|Hawaiian||sky, heaven|
Lehua|g|Hawaiian|Hawaiian||the ʻōhiʻa lehua blossom|
Lei|g|Hawaiian|Hawaiian||flower garland; beloved|
Leialoha|g|Hawaiian|Hawaiian||lei of love|
Leimomi|g|Hawaiian|Hawaiian||pearl lei|
Leinani|g|Hawaiian|Hawaiian||beautiful lei|
Lepeka|g|Hawaiian|Hawaiian|Christian|Rebecca|
Lilinoe|g|Hawaiian|Hawaiian||fine mist|goddess of the mists of Maunakea
Lono|b|Hawaiian|Hawaiian||god of agriculture and peace|
Lāhela|g|Hawaiian|Hawaiian|Christian|Rachel|
Makana|e|Hawaiian|Hawaiian||gift|
Makamae|e|Hawaiian|Hawaiian||precious|
Makoa|b|Hawaiian|Hawaiian||courageous|
Maleko|b|Hawaiian|Hawaiian|Christian|Mark|
Mililani|e|Hawaiian|Hawaiian||praised by the heavens|
Moani|g|Hawaiian|Hawaiian||fragrant breeze|
Moke|b|Hawaiian|Hawaiian|Christian|Moses|
Mokihana|g|Hawaiian|Hawaiian||a fragrant berry of Kauaʻi|
Momi|g|Hawaiian|Hawaiian||pearl|
Momilani|g|Hawaiian|Hawaiian||heavenly pearl|
Māhealani|g|Hawaiian|Hawaiian||night of the full moon|
Mālie|g|Hawaiian|Hawaiian||calm, gentle|
Māpuana|g|Hawaiian|Hawaiian||fragrance|
Māui|b|Hawaiian|Hawaiian||the demigod who fished up the islands|
Nakoa|b|Hawaiian|Hawaiian||the warriors|
Nalani|g|Hawaiian|Hawaiian||the heavens|
Nanea|g|Hawaiian|Hawaiian||tranquil, relaxing|
Nani|g|Hawaiian|Hawaiian||beautiful|
Noelani|g|Hawaiian|Hawaiian||heavenly mist|
Nohea|e|Hawaiian|Hawaiian||handsome, lovely|
Pele|g|Hawaiian|Hawaiian||goddess of fire and volcanoes|
Pua|g|Hawaiian|Hawaiian||flower|
Pualani|g|Hawaiian|Hawaiian||heavenly flower|
Ululani|g|Hawaiian|Hawaiian||heavenly inspiration|
Wailani|e|Hawaiian|Hawaiian||heavenly water|
Waiola|e|Hawaiian|Hawaiian||water of life|
Maile|g|Hawaiian|Hawaiian||the maile vine, used for leis|
Nāmaka|e|Hawaiian|Hawaiian||the eyes|
Timoci|b|Fijian|Fijian|Christian|Timothy|
Tomasi|b|Fijian|Fijian|Christian|Thomas|
Josefa|b|Fijian|Fijian|Christian|Joseph|
Jone|b|Fijian|Fijian|Christian|John|
Inoke|b|Fijian|Fijian|Christian|Enoch|
Isikeli|b|Fijian|Fijian|Christian|Ezekiel|
Apisai|b|Fijian|Fijian|Christian|Abishai|
Samisoni|b|Fijian|Fijian|Christian|Samson|
Sakiusa|b|Fijian|Fijian|Christian|Zacchaeus|
Peni|b|Fijian|Fijian|Christian|Ben|
Isireli|b|Fijian|Fijian|Christian|Israel|
Joritani|b|Fijian|Fijian|Christian|Jordan|
Litia|g|Fijian|Fijian|Christian|Lydia|
Losana|g|Fijian|Fijian|Christian|Rosanna|
Losalini|g|Fijian|Fijian|Christian|Rosaline|
Ateca|g|Fijian|Fijian|Christian|Agatha|
Akanisi|g|Fijian|Fijian|Christian|Agnes|
Unaisi|g|Fijian|Fijian|Christian|Eunice|
Vereniki|g|Fijian|Fijian|Christian|Veronica|
Elenoa|g|Fijian|Fijian|Christian|Eleanor|
Varanisese|g|Fijian|Fijian|Christian|Frances|
Ana|g|Fijian|Fijian|Christian|Anna|
Elisapeta|g|Māori|Māori|Christian|Elizabeth|
Emere|g|Māori|Māori|Christian|Emily|
Eruera|b|Māori|Māori|Christian|Edward|
Haimona|b|Māori|Māori|Christian|Simon|
Hariata|g|Māori|Māori|Christian|Harriet|
Hāriata|g|Māori|Māori|Christian|Harriet|
Hera|g|Māori|Māori|Christian|Sarah|
Herewini|b|Māori|Māori|Christian|Selwyn|
Himiona|b|Māori|Māori|Christian|Simeon|
Hoana|g|Māori|Māori|Christian|Joanna|
Hoani|b|Māori|Māori|Christian|John|
Hohepa|b|Māori|Māori|Christian|Joseph|
Hōhepa|b|Māori|Māori|Christian|Joseph|
Hone|b|Māori|Māori|Christian|John|
Hōne|b|Māori|Māori|Christian|John|
Hāmiora|b|Māori|Māori|Christian|Samuel|
Hāmuera|b|Māori|Māori|Christian|Samuel|
Hārata|g|Māori|Māori|Christian|Charlotte|
Hēmi|b|Māori|Māori|Christian|James|
Hēnare|b|Māori|Māori|Christian|Henry|
Hēni|g|Māori|Māori|Christian|Jane|
Hōri|b|Māori|Māori|Christian|George|
Hūhana|g|Māori|Māori|Christian|Susanna|
Ihipera|g|Māori|Māori|Christian|Isabella|
Irihāpeti|g|Māori|Māori|Christian|Elizabeth|
Irāia|b|Māori|Māori|Christian|Elijah|
Kararaina|g|Māori|Māori|Christian|Caroline|
Maaka|b|Māori|Māori|Christian|Mark|
Māka|b|Māori|Māori|Christian|Mark|
Matire|g|Māori|Māori|Christian|Matilda|
Matiu|b|Māori|Māori|Christian|Matthew|
Mere|g|Māori|Māori|Christian|Mary|
Mereana|g|Māori|Māori|Christian|Marian|
Mikaere|b|Māori|Māori|Christian|Michael|
Miriama|g|Māori|Māori|Christian|Miriam|
Mākere|g|Māori|Māori|Christian|Margaret|
Māta|g|Māori|Māori|Christian|Martha|
Mātene|b|Māori|Māori|Christian|Martin|
Nīkora|b|Māori|Māori|Christian|Nicholas|
Petera|b|Māori|Māori|Christian|Peter|
Pita|b|Māori|Māori|Christian|Peter|
Pirihira|g|Māori|Māori|Christian|Priscilla|
Piripi|b|Māori|Māori|Christian|Philip|
Pāora|b|Māori|Māori|Christian|Paul|
Rewi|b|Māori|Māori|Christian|Levi|
Rihari|b|Māori|Māori|Christian|Richard|
Ruiha|g|Māori|Māori|Christian|Louisa|
Ruta|g|Māori|Māori|Christian|Ruth|
Rāhera|g|Māori|Māori|Christian|Rachel|
Rāniera|b|Māori|Māori|Christian|Daniel|
Tāniora|b|Māori|Māori|Christian|Daniel|
Rāpata|b|Māori|Māori|Christian|Robert|
Rōpata|b|Māori|Māori|Christian|Robert|
Rāwiri|b|Māori|Māori|Christian|David|
Rēnata|b|Māori|Māori|Christian|Leonard|
Rīpeka|g|Māori|Māori|Christian|Rebecca|
Tame|b|Māori|Māori|Christian|Tom|
Tipene|b|Māori|Māori|Christian|Stephen|
Tīpene|b|Māori|Māori|Christian|Stephen|
Tēpene|b|Māori|Māori|Christian|Stephen|
Tāmati|b|Māori|Māori|Christian|Thomas|
Tāre|b|Māori|Māori|Christian|Charles|
Tīmoti|b|Māori|Māori|Christian|Timothy|
Waata|b|Māori|Māori|Christian|Walter|
Wāta|b|Māori|Māori|Christian|Walter|
Wikitoria|g|Māori|Māori|Christian|Victoria|
Wikitōria|g|Māori|Māori|Christian|Victoria|
Wiremu|b|Māori|Māori|Christian|William|
Wī|b|Māori|Māori|Christian|Will|
Ānaru|b|Māori|Māori|Christian|Andrew|
Ārama|b|Māori|Māori|Christian|Adam|
Īhaka|b|Māori|Māori|Christian|Isaac|
Īhāia|b|Māori|Māori|Christian|Isaiah|
Ōriwa|b|Māori|Māori|Christian|Oliver|
Aroha|g|Māori|Māori||love|
Arohanui|g|Māori|Māori||great love|
Hinemoa|g|Māori|Māori||maiden|heroine of the legend of Hinemoa and Tūtānekai, who swam Lake Rotorua to her love
Hinemoana|g|Māori|Māori||maiden of the sea|
Hinerangi|g|Māori|Māori||maiden of the sky|
Hinewai|g|Māori|Māori||maiden of the water|
Ngaio|e|Māori|Māori||a native coastal tree; clever|
Roimata|g|Māori|Māori||tears|
Moko|b|Māori|Māori||grandchild; traditional tattoo|
Toi|e|Māori|Māori||summit; art|
Reremoana|g|Māori|Māori||flying over the sea|
Morehu|b|Māori|Māori||survivor|
Kahurangi|g|Māori|Māori||treasured, precious|
Mana|e|Māori|Māori||prestige, power, authority|
Marama|e|Māori|Māori||moon; light|
Tama|b|Māori|Māori||son, boy|
Tāne|b|Māori|Māori||man; god of forests and birds|
Wairua|e|Māori|Māori||spirit, soul|
Ataahua|g|Māori|Māori||beautiful|
Rangi|b|Māori|Māori||sky|
Ranginui|b|Māori|Māori||the sky father|
Nikau|b|Māori|Māori||the native nīkau palm|
Kauri|e|Māori|Māori||the giant native kauri tree|
Ariki|b|Māori|Māori||chief, leader|
Māia|g|Māori|Māori||brave, bold|
Mihi|g|Māori|Māori||greeting|
Tūī|e|Māori|Māori||the tūī, a native songbird|
Kōwhai|g|Māori|Māori||the golden-flowered kōwhai tree|
Anahera|g|Māori|Māori||angel|
Kaha|b|Māori|Māori||strong, strength|
Whetū|e|Māori|Māori||star|
Moana|e|Māori|Māori||ocean, sea|
Pania|g|Māori|Māori||a sea maiden of Napier legend|
Āwhina|g|Māori|Māori||help, support|
Pili|b|Swahili|Swahili||second-born|
Tatu|g|Swahili|Swahili||third-born|
Mosi|b|Swahili|Swahili||first-born|
Nyota|g|Swahili|Swahili||star|
Kijana|b|Swahili|Swahili||youth|
Asha|g|Swahili|Swahili||life|
Hamisi|b|Swahili|Swahili||born on Thursday|
Jumaane|b|Swahili|Swahili||born on Tuesday|
Mwanajuma|g|Swahili|Swahili||born on Friday|
Mwajuma|g|Swahili|Swahili||born on Friday|
Nuru|e|Swahili|Swahili||light|
Subira|g|Swahili|Swahili||patience|
Uhuru|e|Swahili|Swahili||freedom|
Wema|e|Swahili|Swahili||goodness, kindness|
Fahari|e|Swahili|Swahili||pride, splendor|
Hodari|b|Swahili|Swahili||capable, strong|
Jasiri|b|Swahili|Swahili||brave|
Kito|e|Swahili|Swahili||jewel|
Mwangaza|e|Swahili|Swahili||light, brightness|
Busara|e|Swahili|Swahili||wisdom|
Heri|e|Swahili|Swahili||blessing, happiness|
Shani|g|Swahili|Swahili||wonder, marvel|
Tabasamu|g|Swahili|Swahili||smile|
Rafiki|e|Swahili|Swahili||friend|
Faraji|b|Swahili|Swahili||consolation, comfort|
Zuberi|b|Swahili|Swahili||strong|
Rashidi|b|Swahili|Swahili|Islamic|rightly guided|
Latifa|g|Swahili|Swahili|Islamic|gentle, kind|
Safiya|g|Swahili|Swahili|Islamic|pure|
Swalehe|b|Swahili|Swahili|Islamic|righteous|
Aisha|g|Swahili|Swahili|Islamic|alive, living|
Fatuma|g|Swahili|Swahili|Islamic|the Swahili form of Fatima|
Mariamu|g|Swahili|Swahili|Christian|Mary|
Daudi|b|Swahili|Swahili|Christian|David|
Yohana|b|Swahili|Swahili|Christian|John|
Salama|e|Swahili|Swahili||safety, peace|
Bahati|e|Swahili|Swahili||good fortune, luck|
Bheki|b|Zulu|Zulu||watch over|
Nokubonga|g|Zulu|Zulu||mother of gratitude|
Nokuzola|g|Zulu|Zulu||mother of calm|
Nqobile|e|Zulu|Zulu||victorious|
Siphesihle|e|Zulu|Zulu||a beautiful gift|
Thuli|g|Zulu|Zulu||quiet, calm|
Jabulani|b|Zulu|Zulu||rejoice, be happy|
Sibusiso|b|Zulu|Zulu||blessing|
Nomsa|g|Zulu|Zulu||mother of kindness|
Nhlanhla|b|Zulu|Zulu||luck, good fortune|
Nonhlanhla|g|Zulu|Zulu||mother of luck|
Thokozani|e|Zulu|Zulu||rejoice|
Mthunzi|b|Zulu|Zulu||shade, shelter|
Njabulo|b|Zulu|Zulu||happiness|
Ntokozo|e|Zulu|Zulu||joy|
Bonginkosi|b|Zulu|Zulu||thank the Lord|
Sibongile|g|Zulu|Zulu||we are thankful|
Thembeka|g|Zulu|Zulu||trustworthy|
Busisiwe|g|Zulu|Zulu||blessed|
Khanyisile|g|Zulu|Zulu||she has brought light|
Lungile|e|Zulu|Zulu||it is good, it is right|
Mbali|g|Zulu|Zulu||flower|
Nolwazi|g|Zulu|Zulu||mother of knowledge|
Sphamandla|b|Zulu|Zulu||gift of strength|
Sanele|e|Zulu|Zulu||we are enough|
Langa|b|Zulu|Zulu||sun|
Zinhle|g|Zulu|Zulu||they are beautiful|
Nosipho|g|Zulu|Zulu||mother of gifts|
Simphiwe|e|Zulu|Zulu||we have been given|
Wandile|b|Zulu|Zulu||increased, grown|
Mpumelelo|b|Zulu|Zulu||success|
Nkosinathi|b|Zulu|Zulu||the Lord is with us|
Nkosana|b|Zulu|Zulu||prince|
Lindokuhle|e|Zulu|Zulu||waiting for good things|
Zandile|g|Zulu|Zulu||they have increased|
Nomthandazo|g|Zulu|Zulu||mother of prayer|
Sinethemba|e|Zulu|Zulu||we have hope|
Lwandle|e|Zulu|Zulu||ocean|
Philani|b|Zulu|Zulu||be well, live|
Sifiso|b|Zulu|Zulu||wish|
Abidemi|e|Yoruba|Yoruba||born while father was away|
Abimbola|g|Yoruba|Yoruba||born with wealth|
Abisola|g|Yoruba|Yoruba||born into wealth|
Abosede|g|Yoruba|Yoruba||born on a holy day|
Adeola|e|Yoruba|Yoruba||crown of honor|
Ajoke|g|Yoruba|Yoruba||one cherished by all|
Arike|g|Yoruba|Yoruba||one seen and cherished|
Arinola|g|Yoruba|Yoruba||one who walks with honor|
Atinuke|g|Yoruba|Yoruba||cared for from the womb|
Ayodeji|b|Yoruba|Yoruba||joy has doubled|
Ayoka|g|Yoruba|Yoruba||one who brings joy all around|
Ayoyinka|e|Yoruba|Yoruba||joy surrounds me|
Bayo|b|Yoruba|Yoruba||joy is found|
Biodun|e|Yoruba|Yoruba||born in a festive season|
Bisola|g|Yoruba|Yoruba||born into wealth|
Bolaji|b|Yoruba|Yoruba||wakes up with wealth|
Bolanle|g|Yoruba|Yoruba||finds wealth at home|
Bukola|g|Yoruba|Yoruba||adds to wealth|
Damilare|b|Yoruba|Yoruba||justify me, vindicate me|
Dupe|g|Yoruba|Yoruba||thanks|
Durodola|b|Yoruba|Yoruba||wait and become wealthy|
Ebunoluwa|e|Yoruba|Yoruba||gift of God|
Eniola|e|Yoruba|Yoruba||person of wealth|
Ewatomi|g|Yoruba|Yoruba||my beauty is enough|
Eyitayo|e|Yoruba|Yoruba||this one surpasses joy|
Folake|g|Yoruba|Yoruba||pampered with wealth|
Folakemi|g|Yoruba|Yoruba||pamper me with wealth|
Folasade|g|Yoruba|Yoruba||honor makes a crown|
Funmilayo|g|Yoruba|Yoruba||give me joy|
Idowu|e|Yoruba|Yoruba||the child born after twins|
Ikeoluwa|e|Yoruba|Yoruba||God's care|
Iretioluwa|e|Yoruba|Yoruba||God's goodness|
Iyabo|g|Yoruba|Yoruba||mother has returned|
Kehinde|e|Yoruba|Yoruba||the second-born twin|
Kikelomo|g|Yoruba|Yoruba||to be pampered and loved|
Kolade|b|Yoruba|Yoruba||brings honor home|
Lanre|b|Yoruba|Yoruba||short for Olanrewaju, wealth keeps moving forward|
Mobolaji|e|Yoruba|Yoruba||I woke up with wealth|
Mojisola|g|Yoruba|Yoruba||I woke up in wealth|
Morenike|g|Yoruba|Yoruba||I have found someone to cherish|
Mosunmola|g|Yoruba|Yoruba||I draw close to wealth|
Moyinoluwa|e|Yoruba|Yoruba||I praise God|
Niniola|g|Yoruba|Yoruba||one who has wealth|
Odunayo|e|Yoruba|Yoruba||a year of joy|
Olaide|e|Yoruba|Yoruba||wealth has come|
Olaitan|e|Yoruba|Yoruba||wealth never ends|
Olajide|b|Yoruba|Yoruba||wealth arises|
Olajumoke|g|Yoruba|Yoruba||everyone gathers to cherish her|
Olakitan|e|Yoruba|Yoruba||wealth does not end|
Olamide|e|Yoruba|Yoruba||my wealth has come|
Olatunbosun|b|Yoruba|Yoruba||wealth returns again|
Olawale|b|Yoruba|Yoruba||wealth has come home|
Olawunmi|g|Yoruba|Yoruba||wealth pleases me|
Olubunmi|g|Yoruba|Yoruba||God gave me this|
Olufunke|g|Yoruba|Yoruba||God gave me to cherish|
Olurotimi|b|Yoruba|Yoruba||God stays with me|
Oluwafemi|b|Yoruba|Yoruba||God loves me|
Oluwasanmi|b|Yoruba|Yoruba||God benefits me|
Oluwasegun|b|Yoruba|Yoruba||God is victorious|
Oluwaseyi|e|Yoruba|Yoruba||God made this|
Oluyemi|e|Yoruba|Yoruba||God befits me|
Omolade|g|Yoruba|Yoruba||a child is a crown|
Omolara|g|Yoruba|Yoruba||children are family|
Omolayo|g|Yoruba|Yoruba||a child is joy|
Opeyemi|e|Yoruba|Yoruba||gratitude befits me|
Oreoluwa|e|Yoruba|Yoruba||gift of God|
Oyeyemi|g|Yoruba|Yoruba||a title befits me|
Oyindamola|g|Yoruba|Yoruba||honey mixed with wealth|
Oyinkansola|g|Yoruba|Yoruba||honey drops into wealth|
Seyi|e|Yoruba|Yoruba||made this (short for Oluwaseyi)|
Temilayo|g|Yoruba|Yoruba||mine is joy|
Temiloluwa|e|Yoruba|Yoruba||I belong to God|
Titilayo|g|Yoruba|Yoruba||eternal joy|
Titilope|g|Yoruba|Yoruba||eternal gratitude|
Tiwalola|g|Yoruba|Yoruba||ours is wealth|
Tolani|g|Yoruba|Yoruba||worthy of wealth|
Tolulope|e|Yoruba|Yoruba||thanks belong to God|
Toluwanimi|e|Yoruba|Yoruba||I belong to God|
Tosin|e|Yoruba|Yoruba||worthy of serving (God)|
Toyin|e|Yoruba|Yoruba||worthy of praise|
Tunde|b|Yoruba|Yoruba||has returned|
Wuraola|g|Yoruba|Yoruba||gold of wealth|
Yemi|e|Yoruba|Yoruba||befits me|
Yemisi|g|Yoruba|Yoruba||honor me|
Yetunde|g|Yoruba|Yoruba||mother has returned|
Yewande|g|Yoruba|Yoruba||mother came back for me|
Yinka|e|Yoruba|Yoruba||surrounds me|
Iyiola|e|Yoruba|Yoruba||honor of wealth|
Oladunni|g|Yoruba|Yoruba||wealth is sweet to have|
Olajuwon|b|Yoruba|Yoruba||wealth surpasses them|
Jimoh|b|Yoruba|Yoruba|Islamic|born on Friday|
Kafayat|g|Yoruba|Yoruba|Islamic|sufficiency|
Kudirat|g|Yoruba|Yoruba|Islamic|power|
Ganiyu|b|Yoruba|Yoruba|Islamic|rich, self-sufficient|
Lamidi|b|Yoruba|Yoruba|Islamic|one who praises|
Bilkisu|g|Yoruba|Yoruba|Islamic|Bilqis, the Queen of Sheba|
Aliyu|b|Yoruba|Yoruba|Islamic|exalted|
Malalai|g|Afghan|Pashto||grief-stricken|Malalai of Maiwand, heroine of the 1880 battle
Zarghona|g|Afghan|Pashto||verdant, green|
Spogmai|g|Afghan|Pashto||moon|
Palwasha|g|Afghan|Pashto||moonbeam, ray of light|
Storai|g|Afghan|Pashto||star|
Wazhma|g|Afghan|Pashto||gentle breeze|
Breshna|g|Afghan|Pashto||lightning|
Torpekai|g|Afghan|Pashto||black-tressed|
Nazo|g|Afghan|Pashto||delicate, tender|Nazo Tokhi, Pashto poet and mother of Mirwais Hotak
Shkula|g|Afghan|Pashto||beautiful|
Pashtana|g|Afghan|Pashto||Pashtun woman|
Durkhanai|g|Afghan|Pashto||pearl-like lady|heroine of the Pashto love legend Adam Khan and Durkhanai
Meena|g|Afghan|Pashto||love|Meena Keshwar Kamal, founder of RAWA
Muska|g|Afghan|Pashto||smile|
Hila|g|Afghan|Pashto||hope|
Hosai|g|Afghan|Pashto||deer|
Shabnam|g|Afghan|Persian||dew|
Mursal|g|Afghan|Arabic||sent one, messenger|
Freshta|g|Afghan|Persian||angel|
Mahbooba|g|Afghan|Arabic||beloved|
Sitara|g|Afghan|Persian||star|
Farkhunda|g|Afghan|Persian||blessed, fortunate|
Roya|g|Afghan|Persian||dream, vision|
Mozhgan|g|Afghan|Persian||eyelashes|
Nilofar|g|Afghan|Persian||water lily|
Zohra|g|Afghan|Arabic||Venus, brightness|Zohra, Afghanistan's first all-women orchestra
Laila|g|Afghan|Arabic||night|
Habiba|g|Afghan|Arabic||beloved|
Ghazal|g|Afghan|Arabic||love poem|
Shogofa|g|Afghan|Persian||blossom|
Tamana|g|Afghan|Persian||wish, desire|
Arezo|g|Afghan|Persian||wish, hope|
Khatera|g|Afghan|Persian||memory|
Muzhda|g|Afghan|Persian||good news|
Parwana|g|Afghan|Persian||moth, butterfly|
Pari|g|Afghan|Persian||fairy|
Rabia|g|Afghan|Arabic||fourth|Rabia Balkhi, 10th-century poet of Balkh
Benazir|g|Afghan|Persian||incomparable|
Gulbadan|g|Afghan|Persian||flower-bodied|Gulbadan Begum, Babur's daughter, born in Kabul
Nargis|g|Afghan|Persian||narcissus|
Nasrin|g|Afghan|Persian||wild rose|
Yasaman|g|Afghan|Persian||jasmine|
Mahtab|g|Afghan|Persian||moonlight|
Mahnaz|g|Afghan|Persian||grace of the moon|
Mahwash|g|Afghan|Persian||moon-like|
Mahjabin|g|Afghan|Persian||moon-browed|
Mahgul|g|Afghan|Persian||moon flower|
Hasina|g|Afghan|Arabic||beautiful|
Jamila|g|Afghan|Arabic||beautiful|
Karima|g|Afghan|Arabic||generous|
Najiba|g|Afghan|Arabic||noble|
Nazanin|g|Afghan|Persian||delicate, charming|
Nooria|g|Afghan|Arabic||luminous|
Nasima|g|Afghan|Arabic||gentle breeze|
Rahima|g|Afghan|Arabic||compassionate|
Sabira|g|Afghan|Arabic||patient|
Sakina|g|Afghan|Arabic|Islamic|tranquility|
Shakila|g|Afghan|Arabic||beautiful, well-formed|
Shukria|g|Afghan|Arabic||thankfulness|
Sima|g|Afghan|Persian||face, visage|
Sohaila|g|Afghan|Arabic||Canopus, a bright star|
Zakia|g|Afghan|Arabic||pure, chaste|
Nazifa|g|Afghan|Arabic||clean, pure|
Nafisa|g|Afghan|Arabic||precious|
Masuma|g|Afghan|Arabic||innocent|
Homa|g|Afghan|Persian||mythical bird of good fortune|
Humaira|g|Afghan|Arabic|Islamic|little red one, rosy|affectionate name of Aisha
Fariba|g|Afghan|Persian||charming|
Farzana|g|Afghan|Persian||wise|
Fawzia|g|Afghan|Arabic||victory, success|
Gulshan|g|Afghan|Persian||rose garden|
Gulbahar|g|Afghan|Persian||spring flower|
Malika|g|Afghan|Arabic||queen|
Naheed|g|Afghan|Persian||Venus|
Nigina|g|Afghan|Persian||gemstone of a ring|
Parwin|g|Afghan|Persian||the Pleiades|
Rangina|g|Afghan|Persian||colorful|
Rukhsar|g|Afghan|Persian||cheek, face|
Rukhshana|g|Afghan|Persian||luminous, shining|Roxana of Bactria, wife of Alexander the Great
Saba|g|Afghan|Arabic||morning breeze|
Sadaf|g|Afghan|Persian||seashell, pearl oyster|
Safia|g|Afghan|Arabic||pure|
Sanam|g|Afghan|Persian||beloved, idol|
Shafiqa|g|Afghan|Arabic||compassionate|
Sughra|g|Afghan|Arabic||youngest, smaller|
Tabasum|g|Afghan|Arabic||smile|
Tahira|g|Afghan|Arabic||pure|
Wahida|g|Afghan|Arabic||unique|
Yalda|g|Afghan|Persian||birth; longest night|Shab-e Yalda, the winter solstice night
Zarifa|g|Afghan|Arabic||graceful|
Zubaida|g|Afghan|Arabic||cream, choicest part|
Asma|g|Afghan|Arabic||lofty, eminent|
Basira|g|Afghan|Arabic||insightful|
Firoza|g|Afghan|Persian||turquoise|
Kamila|g|Afghan|Arabic||perfect, complete|
Sharifa|g|Afghan|Arabic||noble|
Simin|g|Afghan|Persian||silvery|
Sahar|g|Afghan|Arabic||dawn|
Shakiba|g|Afghan|Persian||patient|
Marwa|g|Afghan|Arabic|Islamic|flint stone|hill of Marwa in Mecca
Anisa|g|Afghan|Arabic||friendly companion|
Fahima|g|Afghan|Arabic||intelligent|
Hamida|g|Afghan|Arabic||praiseworthy|
Wajiha|g|Afghan|Arabic||distinguished|
Diba|g|Afghan|Persian||silk brocade|
Sultana|g|Afghan|Arabic||queen, sovereign|
Marjan|g|Afghan|Persian||coral|
Gulnaz|g|Afghan|Persian||graceful as a flower|
Gulchehra|g|Afghan|Persian||flower-faced|
Gulnar|g|Afghan|Persian||pomegranate blossom|
Dilnoza|g|Afghan|Persian||tender-hearted|Uzbek name
Gulnora|g|Afghan|Persian||pomegranate flower|Uzbek name
Dilbar|g|Afghan|Persian||beloved, heart-stealer|
Nodira|g|Afghan|Arabic||rare, precious|Nodira, 19th-century Uzbek poet
Oydin|g|Afghan|Turkic||moonlit, bright|Uzbek name
Yulduz|g|Afghan|Turkic||star|Uzbek name
Mahmud|b|Afghan|Arabic||praised|Mahmud of Ghazni
Mirwais|b|Afghan|Persian||chief Wais|Mirwais Hotak, founder of the Hotak dynasty
Khushal|b|Afghan|Persian||happy, prosperous|Khushal Khan Khattak, warrior-poet
Rahman|b|Afghan|Arabic|Islamic|merciful|Rahman Baba, beloved Pashto Sufi poet
Wais|b|Afghan|Arabic|Islamic|little wolf|Uwais al-Qarani
Zalmai|b|Afghan|Pashto||youth, young man|
Atal|b|Afghan|Pashto||hero|
Baryalai|b|Afghan|Pashto||victorious, successful|
Nangyalai|b|Afghan|Pashto||honorable|
Toryalai|b|Afghan|Pashto||brave, sword-wielding|
Lemar|b|Afghan|Pashto||sun|
Zmarai|b|Afghan|Pashto||lion|
Sher|b|Afghan|Persian||lion|
Shir|b|Afghan|Persian||lion|
Jawed|b|Afghan|Persian||eternal|
Aziz|b|Afghan|Arabic||dear, mighty|
Hamid|b|Afghan|Arabic||praiseworthy|
Rahim|b|Afghan|Arabic||merciful|
Wahid|b|Afghan|Arabic||unique, one|
Mustafa|b|Afghan|Arabic|Islamic|chosen|epithet of the Prophet Muhammad
Rustam|b|Afghan|Persian||strong-bodied|hero of the Shahnameh
Massoud|b|Afghan|Arabic||fortunate|Ahmad Shah Massoud, "Lion of Panjshir"
Tamim|b|Afghan|Arabic||complete, perfect|
Hekmat|b|Afghan|Arabic||wisdom|
Najib|b|Afghan|Arabic||noble|
Ghazi|b|Afghan|Arabic||warrior|
Abdullah|b|Afghan|Arabic|Islamic|servant of God|
Akbar|b|Afghan|Arabic||greatest|
Amin|b|Afghan|Arabic||trustworthy|
Ashraf|b|Afghan|Arabic||most noble|
Asad|b|Afghan|Arabic||lion|
Babur|b|Afghan|Persian||tiger|Babur, Mughal founder, buried in Kabul's Bagh-e Babur
Daud|b|Afghan|Hebrew|Islamic|beloved|the prophet David
Ehsan|b|Afghan|Arabic||kindness|
Elyas|b|Afghan|Hebrew|Islamic|my God is Yahweh|the prophet Elijah
Fahim|b|Afghan|Arabic||intelligent|
Farid|b|Afghan|Arabic||unique|
Fawad|b|Afghan|Arabic||heart|
Habib|b|Afghan|Arabic||beloved|
Hafiz|b|Afghan|Arabic|Islamic|guardian; one who knows the Qur'an by heart|
Haidar|b|Afghan|Arabic|Islamic|lion|epithet of Ali ibn Abi Talib
Hasan|b|Afghan|Arabic|Islamic|good, handsome|grandson of the Prophet
Husain|b|Afghan|Arabic|Islamic|little good one|grandson of the Prophet
Homayoun|b|Afghan|Persian||fortunate, royal|Humayun, Mughal emperor
Ishaq|b|Afghan|Hebrew|Islamic|he laughs|the prophet Isaac
Jalal|b|Afghan|Arabic||majesty|Jalal ad-Din Rumi, born in Balkh
Jamil|b|Afghan|Arabic||handsome|
Jawad|b|Afghan|Arabic||generous|
Kamal|b|Afghan|Arabic||perfection|
Mansur|b|Afghan|Arabic||victorious|
Murad|b|Afghan|Arabic||wish, desire|
Nabi|b|Afghan|Arabic|Islamic|prophet|
Nadir|b|Afghan|Arabic||rare|Mohammed Nadir Shah, king of Afghanistan
Naeem|b|Afghan|Arabic||bliss|
Nasir|b|Afghan|Arabic||helper|
Nawid|b|Afghan|Persian||good news|
Roshan|e|Afghan|Persian||bright, light|
Omid|b|Afghan|Persian||hope|
Omar|b|Afghan|Arabic|Islamic|long-lived, flourishing|Umar, second caliph
Parwiz|b|Afghan|Persian||victorious|
Qasim|b|Afghan|Arabic||distributor|
Sadiq|b|Afghan|Arabic||truthful|
Saeed|b|Afghan|Arabic||happy, fortunate|
Salim|b|Afghan|Arabic||safe, sound|
Shafiq|b|Afghan|Arabic||compassionate|
Shahzad|b|Afghan|Persian||prince|
Siddiq|b|Afghan|Arabic|Islamic|truthful|Abu Bakr al-Siddiq
Wali|b|Afghan|Arabic||guardian, friend of God|
Yaqub|b|Afghan|Hebrew|Islamic|supplanter|the prophet Jacob
Yousuf|b|Afghan|Hebrew|Islamic|God increases|the prophet Joseph
Zahir|b|Afghan|Arabic||evident, helper|Mohammed Zahir Shah, last king of Afghanistan
Zia|b|Afghan|Arabic||light|
Zubair|b|Afghan|Arabic||strong, firm|
Shirzad|b|Afghan|Persian||lion-born|
Dilawar|b|Afghan|Persian||brave|
Bahadur|b|Afghan|Turkic||brave, hero|
Timur|b|Afghan|Turkic||iron|
Arsalan|b|Afghan|Turkic||lion|
Bakhtiar|b|Afghan|Persian||fortunate|
Farrukh|b|Afghan|Persian||fortunate, happy|
Behruz|b|Afghan|Persian||fortunate, good day|
Bahram|b|Afghan|Persian||victorious|
Mahdi|b|Afghan|Arabic|Islamic|rightly guided|
Reza|b|Afghan|Arabic|Islamic|contentment|Imam Reza
Abbas|b|Afghan|Arabic|Islamic|stern, lion|Abbas ibn Ali
Qurban|b|Afghan|Arabic|Islamic|sacrifice|
Khalil|b|Afghan|Arabic|Islamic|friend|epithet of the prophet Abraham
Kamran|b|Afghan|Persian||successful|
Iqbal|b|Afghan|Arabic||good fortune|
Shams|b|Afghan|Arabic||sun|
Sakhi|b|Afghan|Arabic||generous|Karte Sakhi shrine in Kabul
Shahab|b|Afghan|Arabic||shooting star|
Shaheen|b|Afghan|Persian||falcon|
Sohail|b|Afghan|Arabic||Canopus, a bright star|
Jahangir|b|Afghan|Persian||world-conqueror|
Ajmal|b|Afghan|Arabic||most beautiful|
Hashmat|b|Afghan|Arabic||dignity|
Mujtaba|b|Afghan|Arabic|Islamic|chosen|epithet of Imam Hasan
Rasul|b|Afghan|Arabic|Islamic|messenger|
Yasin|b|Afghan|Arabic|Islamic|Ya-Sin, a chapter of the Qur'an|
Zakaria|b|Afghan|Hebrew|Islamic|God remembers|the prophet Zechariah
Amanullah|b|Afghan|Arabic|Islamic|protection of God|King Amanullah Khan, who won independence in 1919
Zabihullah|b|Afghan|Arabic|Islamic|sacrifice to God|
Najibullah|b|Afghan|Arabic|Islamic|noble one of God|
Nasrullah|b|Afghan|Arabic|Islamic|help of God|
Habibullah|b|Afghan|Arabic|Islamic|beloved of God|Habibullah Khan, emir of Afghanistan
Rahmatullah|b|Afghan|Arabic|Islamic|mercy of God|
Inayatullah|b|Afghan|Arabic|Islamic|grace of God|
Ataullah|b|Afghan|Arabic|Islamic|gift of God|
Asadullah|b|Afghan|Arabic|Islamic|lion of God|
Saifullah|b|Afghan|Arabic|Islamic|sword of God|
Rohullah|b|Afghan|Arabic|Islamic|spirit of God|epithet of Jesus in Islam
Thiago|b|Argentine|Hebrew|Christian|supplanter|from Santiago (Saint James); a top boys' name in Argentina
Bautista|b|Argentine|Greek|Christian|baptizer|honors Saint John the Baptist
Valentino|b|Argentine|Latin||strong, healthy|Italian form, popular among Argentines of Italian heritage
Valentín|b|Argentine|Latin|Christian|strong, healthy|Saint Valentine
Felipe|b|Argentine|Greek||lover of horses|
Facundo|b|Argentine|Latin||eloquent|Facundo Quiroga, caudillo in Sarmiento's classic "Facundo"
Agustín|b|Argentine|Latin|Christian|venerable, majestic|Saint Augustine
Ignacio|b|Argentine|Latin|Christian|fiery|Saint Ignatius of Loyola
Franco|b|Argentine|Germanic||free, a Frank|
Ezequiel|b|Argentine|Hebrew||God strengthens|the prophet Ezekiel
Maximiliano|b|Argentine|Latin||greatest|
Lionel|b|Argentine|French||little lion|Lionel Messi
Leonel|b|Argentine|French||little lion|
Gastón|b|Argentine|French||man from Gascony|
Hernán|b|Argentine|Germanic||bold voyager|form of Fernando
Germán|b|Argentine|Latin||brother|
Leandro|b|Argentine|Greek||lion-man|
Julián|b|Argentine|Latin||of the Julius family, youthful|Julián Álvarez, World Cup champion
Emiliano|b|Argentine|Latin||rival, eager|
Matías|b|Argentine|Hebrew|Christian|gift of God|Saint Matthias
Santino|b|Argentine|Italian|Christian|little saint|very popular Italian-heritage name in Argentina
Bruno|b|Argentine|Germanic||brown|
Renzo|b|Argentine|Italian||from Laurentum|Italian short form of Lorenzo
Tomás|b|Argentine|Aramaic|Christian|twin|Saint Thomas the Apostle
Lucas|b|Argentine|Greek|Christian|man from Lucania|Saint Luke the Evangelist
Martín|b|Argentine|Latin||of Mars|José de San Martín, liberator of Argentina
Nicolás|b|Argentine|Greek||victory of the people|
Dante|b|Argentine|Latin||enduring|Dante Alighieri
Simón|b|Argentine|Hebrew||he has heard|
Alejo|b|Argentine|Greek||defender|
Rodrigo|b|Argentine|Germanic||famous ruler|Rodrigo De Paul, World Cup champion
Patricio|b|Argentine|Latin|Christian|nobleman|Saint Patrick
Ramiro|b|Argentine|Germanic||famous counsel|
Esteban|b|Argentine|Greek|Christian|crown|Saint Stephen
Néstor|b|Argentine|Greek||homecoming|Néstor Kirchner, president of Argentina
Ernesto|b|Argentine|Germanic||serious, resolute|Ernesto "Che" Guevara, born in Rosario
Domingo|b|Argentine|Latin|Christian|of the Lord|Domingo Faustino Sarmiento
Manuel|b|Argentine|Hebrew||God is with us|Manuel Belgrano, creator of the Argentine flag
Emanuel|b|Argentine|Hebrew||God is with us|
Bernardo|b|Argentine|Germanic||brave as a bear|Bernardo Houssay, Argentina's first science Nobel
Jorge|b|Argentine|Greek||farmer|Jorge Luis Borges; Jorge Bergoglio (Pope Francis)
Francisco|b|Argentine|Latin|Christian|Frenchman, free one|Pope Francis, born in Buenos Aires
Carlos|b|Argentine|Germanic||free man|Carlos Gardel, the voice of tango
Mariano|b|Argentine|Latin||of Marius|Mariano Moreno, hero of the May Revolution
Cornelio|b|Argentine|Latin||horn|Cornelio Saavedra, head of the First Junta
Hipólito|b|Argentine|Greek||freer of horses|Hipólito Yrigoyen, president of Argentina
Bartolomé|b|Argentine|Aramaic|Christian|son of Talmai|Bartolomé Mitre, president of Argentina
Elías|b|Argentine|Hebrew||my God is Yahweh|the prophet Elijah
Fausto|b|Argentine|Latin||fortunate|
Enzo|b|Argentine|Italian||ruler of the home|Enzo Fernández, World Cup champion
Luciano|b|Argentine|Latin||light|
Gerónimo|b|Argentine|Greek|Christian|sacred name|Saint Jerome
Fabricio|b|Argentine|Latin||craftsman|
Marcos|b|Argentine|Latin|Christian|dedicated to Mars|Saint Mark the Evangelist
Juan|b|Argentine|Hebrew|Christian|God is gracious|Juan Perón, president of Argentina
Claudio|b|Argentine|Latin||lame|
Pablo|b|Argentine|Latin|Christian|small|Saint Paul
Andrés|b|Argentine|Greek|Christian|manly|Saint Andrew
Adrián|b|Argentine|Latin||from Hadria|
Cristian|b|Argentine|Greek|Christian|follower of Christ|
Ángel|b|Argentine|Greek|Christian|messenger|Ángel Di María, World Cup champion
Rubén|b|Argentine|Hebrew||behold, a son|
Darío|b|Argentine|Persian||he who holds firm the good|
Eduardo|b|Argentine|English||wealthy guardian|
Osvaldo|b|Argentine|English||divine power|
Salvador|b|Argentine|Latin|Christian|savior|
Jeremías|b|Argentine|Hebrew||God will exalt|
Abel|b|Argentine|Hebrew||breath|
Teo|b|Argentine|Greek||god|
Martina|g|Argentine|Latin||of Mars|
Catalina|g|Argentine|Greek|Christian|pure|Saint Catherine
Delfina|g|Argentine|Greek||dolphin|
Morena|g|Argentine|Spanish||dark-haired, brunette|
Mora|g|Argentine|Spanish||blackberry|
Milagros|g|Argentine|Spanish|Christian|miracles|Our Lady of Miracles
Agustina|g|Argentine|Latin||venerable, majestic|
Florencia|g|Argentine|Latin||flourishing|
Micaela|g|Argentine|Hebrew||who is like God?|
Rocío|g|Argentine|Spanish|Christian|dew|Our Lady of El Rocío
Abril|g|Argentine|Spanish||April|
Mía|g|Argentine|Spanish||mine|
Luján|g|Argentine|Spanish|Christian|of Luján|Our Lady of Luján, patroness of Argentina
Celeste|g|Argentine|Latin||heavenly, sky blue|the celeste of the Argentine flag
Antonella|g|Argentine|Italian||of the Antonius family|Italian-heritage favorite; Antonela Roccuzzo
Eva|g|Argentine|Hebrew||life|Eva "Evita" Perón
Malvina|g|Argentine|Scottish Gaelic||smooth brow|also evokes the Malvinas (Falkland) Islands
Sofía|g|Argentine|Greek||wisdom|
Isabella|g|Argentine|Hebrew||pledged to God|
Olivia|g|Argentine|Latin||olive tree|
Josefina|g|Argentine|Hebrew||God will add|
Julieta|g|Argentine|Latin||youthful|
Pilar|g|Argentine|Spanish|Christian|pillar|Our Lady of the Pillar
Mercedes|g|Argentine|Spanish|Christian|mercies|Mercedes Sosa, voice of Argentine folk music
Juana|g|Argentine|Hebrew||God is gracious|Juana Azurduy, heroine of independence
Candela|g|Argentine|Spanish|Christian|candle|Candlemas (Our Lady of Candelaria)
Ludmila|g|Argentine|Slavic||loved by the people|
Pía|g|Argentine|Latin||pious|
Clara|g|Argentine|Latin|Christian|clear, bright|Saint Clare of Assisi
Alma|g|Argentine|Spanish||soul|
Luz|g|Argentine|Spanish|Christian|light|Our Lady of Light
Sol|g|Argentine|Spanish||sun|the Sun of May on the Argentine flag
Jazmín|g|Argentine|Persian||jasmine|
Maite|g|Argentine|Basque||beloved|
Lourdes|g|Argentine|French|Christian|place name|Our Lady of Lourdes
Soledad|g|Argentine|Spanish|Christian|solitude|Our Lady of Solitude
Belén|g|Argentine|Hebrew|Christian|Bethlehem, house of bread|
Constanza|g|Argentine|Latin||steadfast|
Fiorella|g|Argentine|Italian||little flower|
Giuliana|g|Argentine|Italian||youthful|
Ornella|g|Argentine|Italian||flowering ash tree|
Carolina|g|Argentine|Germanic||free woman|
Natalia|g|Argentine|Latin|Christian|Christmas day|
Gisela|g|Argentine|Germanic||pledge|
Alfonsina|g|Argentine|Germanic||noble and ready|Alfonsina Storni, Argentine poet
Ángeles|g|Argentine|Spanish|Christian|angels|Our Lady of the Angels
Rosario|g|Argentine|Spanish|Christian|rosary|Our Lady of the Rosary; also the city of Rosario
Azul|g|Argentine|Spanish||blue|
Malena|g|Argentine|Hebrew|Christian|woman of Magdala|the classic tango "Malena"
Libertad|g|Argentine|Spanish||freedom|
Esperanza|g|Argentine|Spanish||hope|
Amparo|g|Argentine|Spanish|Christian|protection|Our Lady of Protection
Selva|g|Argentine|Spanish||forest|
Valeria|g|Argentine|Latin||strong, healthy|
Emilia|g|Argentine|Latin||rival, eager|
Guillermina|g|Argentine|Germanic||resolute protector|
Bárbara|g|Argentine|Greek|Christian|foreign|Saint Barbara
Lucila|g|Argentine|Latin||light|
Noelia|g|Argentine|French|Christian|Christmas|
Yamila|g|Argentine|Arabic||beautiful|
Melina|g|Argentine|Greek||honey|
Fernanda|g|Argentine|Germanic||bold voyager|
Tamara|g|Argentine|Hebrew||date palm|
Nahuel|b|Mapuche|Mapudungun||jaguar|
Lautaro|b|Mapuche|Mapudungun||swift hawk|Leftraru, Mapuche toqui who fought the Spanish
Ayelén|g|Mapuche|Mapudungun||joy|
Rayén|g|Mapuche|Mapudungun||flower|
Millaray|g|Mapuche|Mapudungun||golden flower|
Ailín|g|Mapuche|Mapudungun||transparent, clear|
Antú|b|Mapuche|Mapudungun||sun|
Pehuén|e|Mapuche|Mapudungun||araucaria tree|the sacred pine of the Pehuenche people
Liwen|g|Mapuche|Mapudungun||dawn light|
Nehuén|b|Mapuche|Mapudungun||strength|
Relmu|g|Mapuche|Mapudungun||rainbow|
Quimey|g|Mapuche|Mapudungun||beautiful|
Aliwen|e|Mapuche|Mapudungun||tree|
Cuyén|g|Mapuche|Mapudungun||moon|
Painé|g|Mapuche|Mapudungun||sky blue|
Itatí|g|Guaraní|Guaraní|Christian|white stone|Our Lady of Itatí, patroness of Corrientes
Jasy|g|Guaraní|Guaraní||moon|
Ará|e|Guaraní|Guaraní||day, sky|
Arami|g|Guaraní|Guaraní||piece of sky|
Mainumby|e|Guaraní|Guaraní||hummingbird|
Yeruti|g|Guaraní|Guaraní||turtledove|
Irupé|g|Guaraní|Guaraní||water lily|the giant water lily of the Paraná
Yvoty|g|Guaraní|Guaraní||flower|
Poty|g|Guaraní|Guaraní||flower|
Panambí|g|Guaraní|Guaraní||butterfly|
Ñasaindy|g|Guaraní|Guaraní||moonlight|
Ysapy|g|Guaraní|Guaraní||dew|
Arandú|b|Guaraní|Guaraní||wise|
Kuarahy|b|Guaraní|Guaraní||sun|
Anahit|g|Armenian|Armenian||goddess of fertility and wisdom|the ancient Armenian goddess Anahit
Ani|g|Armenian|Armenian||from the medieval Armenian capital Ani|Ani, the "city of 1001 churches"
Lusine|g|Armenian|Armenian||moon|
Lusik|g|Armenian|Armenian||little light|
Siranush|g|Armenian|Armenian||sweet love|
Siran|g|Armenian|Armenian||lovely, beloved|
Arpi|g|Armenian|Armenian||sun, light|
Arpine|g|Armenian|Armenian||sunrise|
Astghik|g|Armenian|Armenian||little star|Astghik, Armenian goddess of love and beauty
Tatevik|g|Armenian|Armenian||little Tatev, "give wings"|after Tatev Monastery in Syunik
Hasmik|g|Armenian|Armenian||jasmine|
Gayane|g|Armenian|Greek|Christian|of the earth|Saint Gayane, abbess martyred with Saint Hripsime
Shushan|g|Armenian|Hebrew||lily|
Shushanik|g|Armenian|Hebrew|Christian|little lily|Saint Shushanik, Armenian princess martyred in Georgia
Naira|g|Armenian|Akkadian||woman of Nairi, old name for Armenia|
Nver|g|Armenian|Armenian||gift|
Zabel|g|Armenian|Hebrew||God is my oath|Zabel Yesayan, Armenian novelist
Zepyur|g|Armenian|Greek||west wind|
Lilit|g|Armenian|Hebrew||of the night|
Anoush|g|Armenian|Armenian||sweet|Anoush, opera by Armen Tigranian
Arev|g|Armenian|Armenian||sun|
Arevik|g|Armenian|Armenian||little sun|
Gohar|g|Armenian|Persian||jewel, gem|
Margarit|g|Armenian|Greek||pearl|
Vard|g|Armenian|Armenian||rose|
Vardush|g|Armenian|Armenian||little rose|
Vardanush|g|Armenian|Armenian||sweet rose|
Varduhi|g|Armenian|Armenian||rose lady|
Alvard|g|Armenian|Armenian||red rose|
Shoghik|g|Armenian|Armenian||little ray of light|
Shoghakat|g|Armenian|Armenian|Christian|drop of light|Shoghakat Church in Vagharshapat
Nazeli|g|Armenian|Persian||delicate, charming|
Nazik|g|Armenian|Persian||delicate, tender|
Armine|g|Armenian|Armenian||Armenian woman|
Armenuhi|g|Armenian|Armenian||Armenian woman|
Hayuhi|g|Armenian|Armenian||Armenian woman|
Haykanush|g|Armenian|Armenian||sweet Armenian|
Manushak|g|Armenian|Armenian||violet|
Nunufar|g|Armenian|Persian||water lily|
Tsaghik|g|Armenian|Armenian||little flower|
Yeghisabet|g|Armenian|Hebrew|Christian|God is my oath|
Taguhi|g|Armenian|Armenian||queen|
Ishkhanuhi|g|Armenian|Armenian||princess|
Srbuhi|g|Armenian|Armenian|Christian|holy woman|
Aghavni|g|Armenian|Armenian||dove|
Arusyak|g|Armenian|Armenian||the planet Venus, morning star|
Azniv|g|Armenian|Armenian||noble, honest|
Zvart|g|Armenian|Armenian||cheerful, merry|
Knarik|g|Armenian|Armenian||little lyre|
Sirvard|g|Armenian|Armenian||rose of love|
Gyulnara|g|Armenian|Persian||pomegranate flower|
Maral|g|Armenian|Persian||doe, deer|
Almast|g|Armenian|Persian||diamond|Almast, opera by Alexander Spendiaryan
Tsovinar|g|Armenian|Armenian||of the sea; goddess of rain|Tsovinar, fiery water goddess of Armenian myth
Arshaluys|g|Armenian|Armenian||dawn, daybreak|
Yerjanik|g|Armenian|Armenian||happy one|
Sofya|g|Armenian|Greek||wisdom|
Yeva|g|Armenian|Hebrew||life|
Marta|g|Armenian|Aramaic||lady, mistress|
Kristine|g|Armenian|Greek|Christian|follower of Christ|
Roza|g|Armenian|Latin||rose|
Nairi|e|Armenian|Akkadian||ancient name of the Armenian highlands|
Sevan|e|Armenian|Armenian||after Lake Sevan|Lake Sevan, the "blue pearl of Armenia"
Hayk|b|Armenian|Armenian||the legendary forefather of Armenians|Hayk slew the tyrant Bel; Armenians call themselves Hay
Haykaz|b|Armenian|Armenian||of the race of Hayk|
Aram|b|Armenian|Armenian||after Aram, legendary Armenian patriarch|Aram Khachaturian, composer of the Sabre Dance
Armen|b|Armenian|Armenian||Armenian|
Armenak|b|Armenian|Armenian||son of Hayk in Armenian legend|
Aramazd|b|Armenian|Persian||wise lord, chief god|Aramazd, father of the gods in Armenian myth
Vahagn|b|Armenian|Persian||victory; god of fire and war|Vahagn the dragon-slayer, born of fire and reed
Mher|b|Armenian|Persian||from Mithra, god of the sun|Mher, hero of the epic David of Sassoun
Tigran|b|Armenian|Persian||sharp, swift as an arrow|Tigran the Great, king of an empire sea to sea
Artashes|b|Armenian|Persian||whose reign is through truth|Artashes I, founder of the Artaxiad dynasty
Trdat|b|Armenian|Persian||given by the god Tir|Trdat III, first Christian king of Armenia
Mihran|b|Armenian|Persian||of Mithra|
Areg|b|Armenian|Armenian||sun|
Arman|b|Armenian|Persian||wish, hope|
Arsen|b|Armenian|Greek||manly, strong|
Levon|b|Armenian|Greek||lion|Levon I, first king of Armenian Cilicia
Davit|b|Armenian|Hebrew||beloved|David of Sassoun, hero of the national epic
Gevorg|b|Armenian|Greek|Christian|farmer|Armenian form of Saint George
Grigor|b|Armenian|Greek|Christian|watchful|Saint Grigor the Illuminator, who converted Armenia
Hovhannes|b|Armenian|Hebrew|Christian|God is gracious|Hovhannes Tumanyan, beloved national poet
Hakob|b|Armenian|Hebrew|Christian|held by the heel|
Hovsep|b|Armenian|Hebrew|Christian|he will add|
Harutyun|b|Armenian|Armenian|Christian|resurrection|
Hambardzum|b|Armenian|Armenian|Christian|ascension|
Khachatur|b|Armenian|Armenian|Christian|given by the cross|Khachatur Abovyan, father of modern Armenian literature
Khachik|b|Armenian|Armenian|Christian|little cross|
Mkrtich|b|Armenian|Armenian|Christian|baptist|after Saint John the Baptist
Karapet|b|Armenian|Armenian|Christian|forerunner|title of Saint John the Baptist
Astvatsatur|b|Armenian|Armenian|Christian|given by God|
Arakel|b|Armenian|Armenian|Christian|apostle|
Galust|b|Armenian|Armenian|Christian|advent, coming|
Avetis|b|Armenian|Armenian|Christian|good news, glad tidings|
Avetik|b|Armenian|Armenian|Christian|good news|
Hayrapet|b|Armenian|Armenian|Christian|patriarch|
Sahak|b|Armenian|Hebrew|Christian|he laughs|Saint Sahak Partev, catholicos who backed the alphabet
Movses|b|Armenian|Hebrew||drawn out of the water|Movses Khorenatsi, father of Armenian history
Yeghishe|b|Armenian|Hebrew|Christian|God is salvation|Yeghishe, chronicler of the Battle of Avarayr
Yeghia|b|Armenian|Hebrew||my God is Yahweh|
Poghos|b|Armenian|Latin|Christian|small, humble|
Andranik|b|Armenian|Armenian||firstborn|General Andranik Ozanian
Nshan|b|Armenian|Armenian||sign, mark|
Shant|b|Armenian|Armenian||lightning|
Shahen|b|Armenian|Persian||royal falcon|
Suren|b|Armenian|Persian||strong, heroic|
Vahan|b|Armenian|Persian||shield|Vahan Mamikonian, 5th-century marzpan
Vrezh|b|Armenian|Armenian||vengeance|
Gurgen|b|Armenian|Persian||wolf|
Ararat|b|Armenian|Armenian||after Mount Ararat|the sacred mountain on the Armenian coat of arms
Masis|b|Armenian|Armenian||Armenian name for Mount Ararat|
Barsegh|b|Armenian|Greek|Christian|royal, kingly|
Kristapor|b|Armenian|Greek|Christian|bearer of Christ|
Manuk|b|Armenian|Armenian||child, infant|
Martiros|b|Armenian|Greek|Christian|martyr, witness|
Mikayel|b|Armenian|Hebrew|Christian|who is like God?|
Norayr|b|Armenian|Armenian||new man|
Zhirayr|b|Armenian|Armenian||lively man|
Hrach|b|Armenian|Armenian||fiery-eyed|
Hrayr|b|Armenian|Armenian||fiery man|
Stepan|b|Armenian|Greek|Christian|crown, garland|
Toros|b|Armenian|Greek|Christian|gift of God|Toros Roslin, medieval manuscript illuminator
Tovmas|b|Armenian|Aramaic|Christian|twin|
Hovnan|b|Armenian|Hebrew||dove|
Yeprem|b|Armenian|Hebrew||fruitful|
Ghazar|b|Armenian|Hebrew|Christian|God has helped|Ghazar Parpetsi, 5th-century historian
Hovakim|b|Armenian|Hebrew|Christian|raised up by God|
Matevos|b|Armenian|Hebrew|Christian|gift of God|
Ghukas|b|Armenian|Greek|Christian|from Lucania|Armenian form of Saint Luke
Markos|b|Armenian|Latin|Christian|of Mars|Armenian form of Saint Mark
Nikoghayos|b|Armenian|Greek|Christian|victory of the people|
Anania|b|Armenian|Hebrew||God has been gracious|Anania Shirakatsi, 7th-century mathematician
Narek|b|Armenian|Armenian|Christian|from Narek|Saint Gregory of Narek, mystic poet
Raffi|b|Armenian|Hebrew||God heals|Raffi, beloved 19th-century Armenian novelist
Samvel|b|Armenian|Hebrew||God has heard|
Garnik|b|Armenian|Armenian||little lamb|
Ishkhan|b|Armenian|Armenian||prince|
Takvor|b|Armenian|Armenian||king|
Azat|b|Armenian|Armenian||free|
Gaspar|b|Armenian|Persian||treasurer|
Baghdasar|b|Armenian|Akkadian||Bel protect the king|
Salomé|g|Colombian|Hebrew|Christian|peace|Salome, follower of Jesus present at the empty tomb
Mariana|g|Colombian|Latin|Christian|of Mary|Mariana Pajón, Colombian Olympic BMX champion
Sara|g|Colombian|Hebrew|Jewish,Christian|princess|Sarah, wife of Abraham
Jerónimo|b|Colombian|Greek|Christian|sacred name|Saint Jerome, translator of the Bible
Leidy|g|Colombian|English||lady|a Colombian spelling of English Lady
Yeimy|g|Colombian|Hebrew||supplanter|a Colombian spelling of Jamie, from Jacob
Jhon|b|Colombian|Hebrew|Christian|God is gracious|a Colombian spelling of English John
Jairo|b|Colombian|Hebrew|Christian|he enlightens|Jairus, whose daughter Jesus raised
Luciana|g|Colombian|Latin||light|
Gabriela|g|Colombian|Hebrew|Christian|God is my strength|
Daniela|g|Colombian|Hebrew|Christian|God is my judge|
Manuela|g|Colombian|Hebrew|Christian|God is with us|Manuela Beltrán, Colombian independence heroine
Policarpa|g|Colombian|Greek||much fruit|Policarpa Salavarrieta, "La Pola," heroine of independence
Sebastián|b|Colombian|Greek|Christian|venerable|Saint Sebastian
Emmanuel|b|Colombian|Hebrew|Christian|God is with us|
Fabián|b|Colombian|Latin||bean grower|
Yeison|b|Colombian|Greek||healer|a Colombian spelling of Jason
Brayan|b|Colombian|Celtic||high, noble|a Colombian spelling of Brian
Stiven|b|Colombian|Greek||crown|a Colombian spelling of Steven
Susana|g|Colombian|Hebrew|Christian|lily|
Laura|g|Colombian|Latin|Christian|laurel|Saint Laura Montoya, Colombia's first saint
Shakira|g|Colombian|Arabic||grateful|Shakira, Colombian singer
Remedios|g|Colombian|Spanish|Christian|remedies|Remedios the Beauty in One Hundred Years of Solitude
Úrsula|g|Colombian|Latin|Christian|little bear|Úrsula Iguarán in One Hundred Years of Solitude
Amaranta|g|Colombian|Greek||unfading|Amaranta Buendía in One Hundred Years of Solitude
Aureliano|b|Colombian|Latin||golden|Colonel Aureliano Buendía in One Hundred Years of Solitude
Fermina|g|Colombian|Latin||firm, steadfast|Fermina Daza in Love in the Time of Cholera
Florentino|b|Colombian|Latin||flourishing|Florentino Ariza in Love in the Time of Cholera
Rigoberto|b|Colombian|Germanic||mighty and bright|Rigoberto Urán, Colombian cyclist
Jacobo|b|Colombian|Hebrew|Jewish,Christian|supplanter|
Violeta|g|Colombian|Latin||violet|
Juliana|g|Colombian|Latin||youthful|
Dayana|g|Colombian|Latin||divine|a Colombian spelling of Diana
Yuliana|g|Colombian|Latin||youthful|a Colombian spelling of Juliana
Altagracia|g|Dominican|Spanish|Christian|high grace|Our Lady of Altagracia, patroness of the Dominican Republic
Consuelo|g|Dominican|Spanish|Christian|consolation|Our Lady of Consolation
Socorro|g|Dominican|Spanish|Christian|help, aid|Our Lady of Perpetual Help
Rosa|g|Dominican|Latin|Christian|rose|Saint Rose of Lima
Clarisa|g|Dominican|Latin||clear, bright|
Fiordaliza|g|Dominican|Italian||lily flower, fleur-de-lis|
Dominga|g|Dominican|Latin|Christian|of the Lord|
Minerva|g|Dominican|Latin||goddess of wisdom|Minerva Mirabal, one of the Mirabal sisters
Patria|g|Dominican|Latin||homeland|Patria Mirabal, one of the Mirabal sisters
Adela|g|Dominican|Germanic||noble|Bélgica Adela "Dedé" Mirabal, the surviving Mirabal sister
Julia|g|Dominican|Latin||youthful|Julia Alvarez, Dominican-American novelist
Ramona|g|Dominican|Germanic||wise protector|
Dulce|g|Dominican|Spanish||sweet|
Raquel|g|Dominican|Hebrew|Jewish,Christian|ewe|Rachel, wife of Jacob
Ángela|g|Dominican|Greek|Christian|messenger, angel|
Anacaona|g|Taíno|Taíno||golden flower|Taíno cacica of Jaragua on Hispaniola
Atabey|g|Taíno|Taíno||mother goddess of the waters|Taíno supreme goddess of fresh water and fertility
Caonabo|b|Taíno|Taíno||lord of the golden house|Taíno cacique of Maguana who resisted Columbus
Yocahu|b|Taíno|Taíno||spirit of the cassava|Taíno supreme god of cassava and the sea
Ramón|b|Dominican|Germanic||wise protector|Matías Ramón Mella, Dominican founding father
Gregorio|b|Dominican|Greek|Christian|watchful|Gregorio Luperón, hero of the Dominican Restoration
Enriquillo|b|Dominican|Germanic||little ruler of the home|Taíno cacique who rebelled against Spanish rule
Yunior|b|Dominican|Latin||younger|a Dominican spelling of English Junior
Luis|b|Dominican|Germanic||famous warrior|Juan Luis Guerra, Dominican singer
Pedro|b|Dominican|Greek|Christian|rock|Pedro Martínez, Dominican Hall of Fame pitcher
Alberto|b|Dominican|Germanic||noble and bright|
Óscar|b|Dominican|Irish||friend of deer|Oscar de la Renta, Dominican fashion designer
Bienvenido|b|Dominican|Spanish||welcome|
Ambiorix|b|Dominican|Gaulish||king who rules all around|Ambiorix, Gaulish chieftain who fought Julius Caesar
Nelson|b|Dominican|English||son of Neil|
Teófilo|b|Dominican|Greek|Christian|friend of God|
Rafael|b|Dominican|Hebrew|Christian|God heals|the archangel Raphael
Danilo|b|Dominican|Hebrew||God is my judge|Danilo Medina, Dominican president
Borinquen|g|Taíno|Taíno||land of the valiant lord|the Taíno name for Puerto Rico
Taína|g|Taíno|Taíno||good, noble|from the Taíno, the island's original people
Roberto|b|Puerto Rican|Germanic||bright fame|Roberto Clemente, Puerto Rican baseball legend
Rita|g|Puerto Rican|Greek|Christian|pearl|Rita Moreno, Puerto Rican actress
Enrique|b|Puerto Rican|Germanic||ruler of the home|Ricky Martin, born Enrique Martín Morales
Sonia|g|Puerto Rican|Greek||wisdom|Sonia Sotomayor, Supreme Court justice of Puerto Rican descent
Eugenio|b|Puerto Rican|Greek||well-born|Eugenio María de Hostos, Puerto Rican educator
Raúl|b|Puerto Rican|Germanic||wolf counsel|Raúl Juliá, Puerto Rican actor
José|b|Puerto Rican|Hebrew|Christian|God will add|José Feliciano, Puerto Rican singer
Ismael|b|Puerto Rican|Hebrew|Jewish,Christian,Islamic|God hears|Ismael Rivera, Puerto Rican sonero
Carmen|g|Puerto Rican|Hebrew|Christian|garden|Our Lady of Mount Carmel
Providencia|g|Puerto Rican|Spanish|Christian|providence|Our Lady of Divine Providence, patroness of Puerto Rico
Monserrate|g|Puerto Rican|Catalan|Christian|serrated mountain|Our Lady of Montserrat, venerated at Hormigueros
Migdalia|g|Puerto Rican|Hebrew||tower|
Wilfredo|b|Puerto Rican|Germanic||desiring peace|
Gilberto|b|Puerto Rican|Germanic||bright pledge|Gilberto Santa Rosa, Puerto Rican salsa singer
Orlando|b|Puerto Rican|Germanic||famous land|Orlando Cepeda, Puerto Rican Hall of Famer
Aracelis|g|Puerto Rican|Latin|Christian|altar of heaven|
Nereida|g|Puerto Rican|Greek||sea nymph|
Elena|g|Puerto Rican|Greek||bright light|
Esmeralda|g|Puerto Rican|Spanish||emerald|
Felisa|g|Puerto Rican|Latin||happy, lucky|Felisa Rincón de Gautier, longtime mayor of San Juan
Pura|g|Puerto Rican|Spanish||pure|Pura Belpré, Puerto Rican librarian and author
Miguel|b|Puerto Rican|Hebrew|Christian|who is like God|the archangel Michael
Benito|b|Puerto Rican|Latin|Christian|blessed|Bad Bunny, born Benito Antonio Martínez Ocasio
Cristina|g|Puerto Rican|Greek|Christian|follower of Christ|
Noemí|g|Puerto Rican|Hebrew|Jewish,Christian|pleasantness|Naomi in the Book of Ruth
Ricardo|b|Puerto Rican|Germanic||brave ruler|
Gloria|g|Puerto Rican|Latin||glory|
Edgardo|b|Puerto Rican|English||wealthy spear|
Norma|g|Puerto Rican|Latin||rule, standard|
Caridad|g|Cuban|Spanish|Christian|charity|Our Lady of Charity of El Cobre, patroness of Cuba
Regla|g|Cuban|Spanish|Christian|rule|Our Lady of Regla, patroness of Havana's bay
Yamilé|g|Cuban|Arabic||beautiful|a Cuban form of Jamila
Yanet|g|Cuban|Hebrew||God is gracious|a Cuban spelling of Janet
Yudith|g|Cuban|Hebrew|Jewish|woman of Judea|a Cuban spelling of Judith
Celia|g|Cuban|Latin||heavenly|Celia Cruz, the Queen of Salsa
Alicia|g|Cuban|Germanic||noble|Alicia Alonso, Cuban prima ballerina
Olga|g|Cuban|Norse||holy, blessed|Olga Guillot, Cuban bolero singer
Fidelia|g|Cuban|Latin||faithful|Ana Fidelia Quirot, Cuban world champion runner
Graciela|g|Cuban|Latin||grace|
Amarilis|g|Cuban|Greek||to sparkle|
Elisa|g|Cuban|Hebrew||God is my oath|
Leticia|g|Cuban|Latin||joy, gladness|
Matilde|g|Cuban|Germanic||mighty in battle|
Estela|g|Cuban|Latin||star|
Gertrudis|g|Cuban|Germanic||spear strength|Gertrudis Gómez de Avellaneda, Cuban poet
Yoel|b|Cuban|Hebrew|Jewish|Yahweh is God|the prophet Joel
Yordan|b|Cuban|Hebrew||to flow down|a Cuban spelling of Jordan
Yoan|b|Cuban|Hebrew||God is gracious|Yoan Moncada, Cuban baseball player
Máximo|b|Cuban|Latin||greatest|Máximo Gómez, general of Cuban independence
Desiderio|b|Cuban|Latin||longing, desire|Desi Arnaz, born Desiderio Arnaz
Dámaso|b|Cuban|Greek|Christian|tamer|Dámaso Pérez Prado, the King of Mambo
Reinaldo|b|Cuban|Germanic||ruler's counsel|Reinaldo Arenas, Cuban writer
Fidel|b|Cuban|Latin||faithful|
Camilo|b|Cuban|Latin||attendant at a religious ceremony|
Orestes|b|Cuban|Greek||of the mountains|Orestes "Minnie" Miñoso, Cuban baseball star
Lázaro|b|Cuban|Hebrew|Christian|God has helped|Saint Lazarus, honored at El Rincón every December 17
Elpidio|b|Cuban|Greek||hope|Elpidio Valdés, beloved Cuban cartoon hero
Silvio|b|Cuban|Latin||of the forest|Silvio Rodríguez, Cuban singer-songwriter
Israel|b|Cuban|Hebrew|Jewish,Christian|he wrestles with God|Israel "Cachao" López, Cuban bassist
Rolando|b|Cuban|Germanic||famous land|
Eliécer|b|Cuban|Hebrew|Jewish,Christian|God is my help|
Bolingo|e|Congolese|Lingala||love|
Elikya|g|Congolese|Lingala||hope|
Esengo|e|Congolese|Lingala||joy|
Kimia|g|Congolese|Lingala||peace|
Elonga|e|Congolese|Lingala||victory|
Matondo|e|Congolese|Lingala||thanks, gratitude|
Nkembo|e|Congolese|Kikongo||glory|
Kiese|e|Congolese|Kikongo||joy|
Makiese|e|Congolese|Kikongo||joys|
Luzolo|g|Congolese|Kikongo||love|
Nzola|g|Congolese|Kikongo||love|
Zola|e|Congolese|Kikongo||love|
Mpasi|e|Congolese|Kikongo||suffering|often given to a child born in a time of hardship
Ndona|g|Congolese|Kikongo||lady|
Mvula|e|Congolese|Kikongo||rain|
Ngoma|b|Congolese|Kikongo||drum|
Nsimba|b|Congolese|Kikongo||the first-born of twins|Kongo twin name; twins were seen as a special blessing
Nzuzi|b|Congolese|Kikongo||the second-born of twins|Kongo twin name, partner name to Nsimba
Nkenge|g|Congolese|Kikongo||twin girl|Kongo twin name
Nlandu|b|Congolese|Kikongo||the one who follows|Kongo name for the child born after twins
Mbuyi|e|Congolese|Tshiluba||the first-born of twins|Luba twin name
Kanku|e|Congolese|Tshiluba||the second-born of twins|Luba twin name, partner name to Mbuyi
Kambale|b|Congolese|Kinande||first-born son|Nande birth-order name from North Kivu
Kavira|g|Congolese|Kinande||first-born daughter|Nande birth-order name from North Kivu
Mugisho|b|Congolese|Mashi||blessing|popular in Bukavu, South Kivu
Ishimwe|e|Congolese|Kinyarwanda||praise, thanksgiving|
Mugisha|b|Congolese|Kinyarwanda||blessing|
Ineza|g|Congolese|Kinyarwanda||goodness, kindness|
Keza|g|Congolese|Kinyarwanda||beautiful one|
Iradukunda|e|Congolese|Kinyarwanda||God loves us|
Habimana|b|Congolese|Kinyarwanda||God exists|
Hakizimana|b|Congolese|Kinyarwanda||God saves|
Niyonkuru|b|Congolese|Kinyarwanda||God is the greatest|
Uwimana|g|Congolese|Kinyarwanda||the one from God|
Kwizera|e|Congolese|Kinyarwanda||faith, trust|
Ihirwe|e|Congolese|Kinyarwanda||good luck|
Ingabire|g|Congolese|Kinyarwanda||gift|
Mahoro|e|Congolese|Kinyarwanda||peace|
Uwamahoro|g|Congolese|Kinyarwanda||the one of peace|
Nshuti|e|Congolese|Kinyarwanda||friend|
Twagirimana|b|Congolese|Kinyarwanda||we have God|
Nizeyimana|b|Congolese|Kinyarwanda||I trust in God|
Bizimana|b|Congolese|Kinyarwanda||God knows|
Tuyishime|e|Congolese|Kinyarwanda||let us give thanks|
Uwera|g|Congolese|Kinyarwanda||the pure one|
Rukundo|b|Congolese|Kinyarwanda||love|
Isimbi|g|Congolese|Kinyarwanda||precious little shell|
Umutesi|g|Congolese|Kinyarwanda||cherished one|
Mutoni|g|Congolese|Kinyarwanda||the favoured one|
Muhire|b|Congolese|Kinyarwanda||fortunate one|
Mapendo|e|Congolese|Swahili||love|
Pendo|g|Congolese|Swahili||love|
Ushindi|b|Congolese|Swahili||victory|
Mwamba|b|Congolese|Swahili||rock|
Chausiku|g|Congolese|Swahili||born at night|
Asifiwe|e|Congolese|Swahili||may he be praised|
Masika|g|Congolese|Swahili||born in the rainy season|
Faraja|g|Congolese|Arabic||comfort, consolation|
Riziki|e|Congolese|Arabic||blessings of provision|
Sifa|g|Congolese|Arabic||praise|
Hekima|g|Congolese|Arabic||wisdom|
Malaika|g|Congolese|Arabic||angel|
Shukuru|b|Congolese|Arabic||thankful|
Safari|b|Congolese|Arabic||journey|
Ramazani|b|Congolese|Arabic|Islamic|born during Ramadan|common in Maniema and Kivu
Shabani|b|Congolese|Arabic|Islamic|born in the month of Sha'ban|
Fatemeh|g|Persian|Arabic|Islamic|one who weans|Fatimah, daughter of the Prophet; long Iran's top girl's name
Zeynab|g|Persian|Arabic|Islamic|fragrant flowering tree|Zaynab, granddaughter of the Prophet, heroine of Karbala
Reyhaneh|g|Persian|Arabic||sweet basil, fragrant herb|
Helma|g|Persian|Arabic||gentle, forbearing|
Hasti|g|Persian|Persian||existence, being|
Baran|g|Persian|Persian||rain|
Setayesh|g|Persian|Persian||praise, worship|
Yasna|g|Persian|Avestan|Zoroastrian|worship, devotion|the Yasna, the central liturgy of the Zoroastrian Avesta
Ava|g|Persian|Persian||voice, sound|
Rosha|g|Persian|Arabic||young gazelle, fawn|
Hosna|g|Persian|Arabic||beauty, goodness|
Mehrsa|g|Persian|Persian||like the sun, kindly|
Mobina|g|Persian|Arabic||clear, manifest|
Parvaneh|g|Persian|Persian||butterfly|
Golnar|g|Persian|Persian||pomegranate blossom|
Mahsa|g|Persian|Persian||like the moon|
Setareh|g|Persian|Persian||star|
Niloufar|g|Persian|Persian||water lily, lotus|
Shadi|g|Persian|Persian||happiness, joy|
Nava|g|Persian|Persian||melody, tune|
Arezoo|g|Persian|Persian||wish, longing|
Gordafarid|g|Persian|Persian||made a champion, hero-born|warrior maiden who fought Sohrab in the Shahnameh
Golnaz|g|Persian|Persian||delicate flower|
Golrokh|g|Persian|Persian||rose-cheeked|
Golshifteh|g|Persian|Persian||in love with flowers|Golshifteh Farahani, actress
Golbahar|g|Persian|Persian||spring flower|
Golsa|g|Persian|Persian||flower-like|
Golpari|g|Persian|Persian||flower fairy|
Golbarg|g|Persian|Persian||flower petal|
Ghoncheh|g|Persian|Persian||rosebud|
Narges|g|Persian|Greek||narcissus flower|Narges Mohammadi, 2023 Nobel Peace Prize laureate
Mina|g|Persian|Persian||azure, enamel|
Mitra|g|Persian|Avestan|Zoroastrian|covenant, friendship|Mithra, ancient Iranian divinity of the covenant and the sun
Roshanak|g|Persian|Old Persian||little star, bright one|Roxana, Bactrian wife of Alexander the Great
Darya|g|Persian|Persian||sea|
Elham|g|Persian|Arabic||inspiration|
Elnaz|g|Persian|Turkic||pride of the people|
Fereshteh|g|Persian|Persian||angel|
Forough|g|Persian|Persian||radiance, brilliance|Forough Farrokhzad, modernist poet
Ghazaleh|g|Persian|Arabic||gazelle|
Leila|g|Persian|Arabic||night|Leili of Nezami's tragic romance Leili and Majnun
Mahshid|g|Persian|Persian||moonlight|
Mahrokh|g|Persian|Persian||moon-faced|
Mahrou|g|Persian|Persian||moon-faced|
Mahvash|g|Persian|Persian||moon-like|
Mahdis|g|Persian|Persian||moon-like|
Mojgan|g|Persian|Persian||eyelashes|
Nahid|g|Persian|Persian||the planet Venus|Persian name of Anahita and of the planet Venus
Negar|g|Persian|Persian||beloved, sweetheart|
Neda|g|Persian|Arabic||call, voice|
Nazila|g|Persian|Persian||delicate, charming|
Nazgol|g|Persian|Persian||delicate flower|
Parastoo|g|Persian|Persian||swallow (bird)|
Pegah|g|Persian|Persian||dawn, early morning|
Raha|g|Persian|Persian||free, released|
Sepideh|g|Persian|Persian||dawn, first light|
Shahrzad|g|Persian|Persian||of noble lineage|Scheherazade, storyteller of the Thousand and One Nights
Soheila|g|Persian|Arabic||the star Canopus|
Parvin|g|Persian|Persian||the Pleiades|Parvin E'tesami, celebrated poet
Taraneh|g|Persian|Persian||song, melody|
Yeganeh|g|Persian|Persian||unique, one of a kind|
Zhaleh|g|Persian|Persian||dew; hail|
Ziba|g|Persian|Persian||beautiful|
Atefeh|g|Persian|Arabic||affection, compassion|
Bahar|g|Persian|Persian||spring|Nowruz, the Persian New Year, falls on the first day of spring
Bahareh|g|Persian|Persian||of the spring|
Delaram|g|Persian|Persian||heart-soothing, beloved|
Donya|g|Persian|Arabic||the world|
Farideh|g|Persian|Arabic||unique, precious pearl|
Farzaneh|g|Persian|Persian||wise, learned|
Hediyeh|g|Persian|Arabic||gift|
Mahboubeh|g|Persian|Arabic||beloved|
Melika|g|Persian|Arabic||queen|
Mehri|g|Persian|Persian||kind, affectionate|
Nasim|e|Persian|Arabic||gentle breeze|
Sayeh|g|Persian|Persian||shade, shadow|
Shahla|g|Persian|Arabic||dark-eyed|
Shahnaz|g|Persian|Persian||pride of the king|
Sheida|g|Persian|Persian||lovelorn, enamored|
Shokoufeh|g|Persian|Persian||blossom|
Sogand|g|Persian|Persian||oath, vow|
Termeh|g|Persian|Persian||fine hand-woven silk cloth|termeh, the traditional brocade of Yazd
Toranj|g|Persian|Persian||citron|
Asal|g|Persian|Arabic||honey|
Armita|g|Persian|Avestan|Zoroastrian|devotion, piety|Spenta Armaiti, Zoroastrian spirit of holy devotion
Bita|g|Persian|Persian||unique, matchless|
Elaheh|g|Persian|Arabic||goddess|
Fataneh|g|Persian|Persian||charming, enchanting|
Mahdieh|g|Persian|Arabic|Islamic|rightly guided|
Maedeh|g|Persian|Arabic|Islamic|table spread with food|Sura al-Ma'ida of the Quran
Masoumeh|g|Persian|Arabic|Islamic|innocent, sinless|Fatemeh Masoumeh, whose shrine stands in Qom
Marzieh|g|Persian|Arabic|Islamic|pleasing to God|epithet of Fatimah, daughter of the Prophet
Kowsar|g|Persian|Arabic|Islamic|abundance; a river of paradise|Sura al-Kawthar of the Quran
Tahereh|g|Persian|Arabic||pure, chaste|Tahereh Qorrat al-Eyn, 19th-century poet
Zohreh|g|Persian|Arabic||the planet Venus|
Monireh|g|Persian|Arabic||radiant, luminous|
Zari|g|Persian|Persian||golden|
Afsaneh|g|Persian|Persian||legend, tale|
Afsoon|g|Persian|Persian||charm, spell|
Nikoo|g|Persian|Persian||good, beautiful|
Avin|g|Persian|Kurdish||love|
Shahdokht|g|Persian|Persian||king's daughter, princess|
Pardis|g|Persian|Old Persian||paradise, walled garden|the Persian pairidaeza, origin of the word paradise
Paniz|g|Persian|Persian||sugar candy|
Shaghayegh|g|Persian|Persian||poppy|
Gisoo|g|Persian|Persian||tresses, long hair|
Taban|g|Persian|Persian||radiant, shining|
Shahrbanoo|g|Persian|Persian||lady of the realm|Shahrbanu, Sasanian princess, wife of Imam Hossein
Banoo|g|Persian|Persian||lady|
Afarin|g|Persian|Persian||praise, bravo|
Arghavan|g|Persian|Persian||Judas tree, purple blossom|
Azar|e|Persian|Persian|Zoroastrian|fire|Azar, ninth month of the Iranian calendar
Banafsheh|g|Persian|Persian||violet|
Dorna|g|Persian|Persian||crane (bird)|
Haleh|g|Persian|Persian||halo around the moon|
Hamideh|g|Persian|Arabic||praiseworthy|
Mojdeh|g|Persian|Persian||good news, glad tidings|
Nastaran|g|Persian|Persian||musk rose|
Noushin|g|Persian|Persian||sweet|
Pooneh|g|Persian|Persian||pennyroyal mint|
Vida|g|Persian|Persian||visible, manifest|
Parnian|g|Persian|Persian||fine painted silk|
Raziyeh|g|Persian|Arabic||content, satisfied|
Shokouh|g|Persian|Arabic||glory, splendor|
Hossein|b|Persian|Arabic|Islamic|little handsome one|Imam Hossein, martyred at Karbala and mourned at Ashura
Abolfazl|b|Persian|Arabic|Islamic|father of virtue|epithet of Abbas ibn Ali, standard-bearer at Karbala
Amirali|b|Persian|Arabic|Islamic|prince Ali|
Amirhossein|b|Persian|Arabic|Islamic|prince Hossein|
Amirmohammad|b|Persian|Arabic|Islamic|prince Mohammad|
Amirreza|b|Persian|Arabic|Islamic|prince Reza|
Alireza|b|Persian|Arabic|Islamic|Ali the content one|honors Imam Reza, Ali ibn Musa al-Reza
Taha|b|Persian|Arabic|Islamic|the letters Ta-Ha opening Sura 20|
Javad|b|Persian|Arabic|Islamic|generous|Imam Javad, ninth Shia Imam
Sajjad|b|Persian|Arabic|Islamic|one who prostrates often|Imam Sajjad, fourth Shia Imam
Hadi|b|Arab|Arabic|Islamic|guide|Written هادي; Imam Hadi, tenth Shia Imam
Mojtaba|b|Persian|Arabic|Islamic|chosen|epithet of Imam Hassan
Mostafa|b|Persian|Arabic|Islamic|chosen one|epithet of the Prophet Muhammad
Morteza|b|Persian|Arabic|Islamic|one pleasing to God|title of Imam Ali
Kazem|b|Persian|Arabic|Islamic|one who restrains anger|Imam Musa al-Kazem, seventh Shia Imam
Sadegh|b|Persian|Arabic|Islamic|truthful|Imam Jafar al-Sadegh, sixth Shia Imam
Bagher|b|Persian|Arabic|Islamic|one who splits open knowledge|Imam Mohammad Bagher, fifth Shia Imam
Mahmoud|b|Persian|Arabic||praised|
Rasoul|b|Persian|Arabic|Islamic|messenger|
Rouhollah|b|Persian|Arabic|Islamic|spirit of God|
Sobhan|b|Persian|Arabic|Islamic|glory be (to God)|
Asghar|b|Persian|Arabic|Islamic|youngest|Ali Asghar, infant son of Imam Hossein at Karbala
Ghasem|b|Persian|Arabic|Islamic|one who distributes|Qasem, son of Imam Hassan, martyred at Karbala
Rayan|b|Persian|Arabic|Islamic|well-watered; gate of paradise|al-Rayyan, the gate of paradise for those who fast
Erfan|b|Persian|Arabic||mystical knowledge, gnosis|
Majid|b|Persian|Arabic||glorious|
Masoud|b|Persian|Arabic||fortunate, lucky|
Mohsen|b|Persian|Arabic||benefactor|
Hamed|b|Persian|Arabic||one who praises|
Vahid|b|Persian|Arabic||unique, singular|
Mobin|b|Persian|Arabic||clear, evident|
Matin|b|Persian|Arabic||firm, steadfast|
Milad|b|Persian|Arabic||birth, birthday|
Aref|b|Persian|Arabic||knower, mystic|Aref Qazvini, poet and songwriter of the Constitutional Revolution
Hafez|b|Persian|Arabic||guardian; one who knows the Quran by heart|Hafez of Shiraz, beloved poet of the Divan
Hesam|b|Persian|Arabic||sharp sword|
Mansour|b|Persian|Arabic||victorious|
Nader|b|Persian|Arabic||rare, precious|Nader Shah, 18th-century conqueror
Sattar|b|Persian|Arabic||one who veils faults|Sattar Khan, hero of the Constitutional Revolution
Soheil|b|Persian|Arabic||the star Canopus|
Taher|b|Persian|Arabic||pure|
Yaser|b|Persian|Arabic||easy, prosperous|
Davoud|b|Persian|Hebrew|Islamic|beloved|the Prophet David
Ebrahim|b|Persian|Hebrew|Islamic|father of multitudes|the Prophet Abraham
Esmaeil|b|Persian|Hebrew|Islamic|God hears|the Prophet Ishmael
Yousef|b|Persian|Hebrew|Islamic|God will increase|the Prophet Joseph
Younes|b|Persian|Hebrew|Islamic|dove|the Prophet Jonah
Danial|b|Persian|Hebrew||God is my judge|the Prophet Daniel, whose tomb is venerated in Shush
Benyamin|b|Persian|Hebrew||son of the right hand|
Ilia|b|Persian|Hebrew||my God is the Lord|
Radin|b|Persian|Persian||generous, noble|
Parsa|b|Persian|Persian||pious, chaste|
Kia|b|Persian|Persian||king, lord|
Bardia|b|Persian|Old Persian||exalted|Bardiya, son of Cyrus the Great
Arian|b|Persian|Persian||noble, Aryan|
Azad|b|Persian|Persian||free|
Behnam|b|Persian|Persian||of good name, reputable|
Behzad|b|Persian|Persian||well-born|Kamal ud-Din Behzad, master of Persian miniature painting
Behrouz|b|Persian|Persian||fortunate, of good days|
Babak|b|Persian|Middle Persian||little father|Babak Khorramdin, 9th-century rebel against the Abbasids
Payam|b|Persian|Persian||message|
Peyman|b|Persian|Persian||promise, covenant|
Pouya|b|Persian|Persian||seeker, striving|
Ramin|b|Persian|Persian||joyful, delighting|hero of the Persian romance Vis and Ramin
Shahin|b|Persian|Persian||royal falcon|
Shahbaz|b|Persian|Persian||royal falcon|
Mehrdad|b|Persian|Persian|Zoroastrian|given by Mithra|Mithridates, name of great Parthian kings
Mehran|b|Persian|Persian||kind, loving|
Mehrzad|b|Persian|Persian||born of kindness|
Farzad|b|Persian|Persian||born of glory|
Keyvan|b|Persian|Persian||the planet Saturn|
Keyhan|b|Persian|Persian||the universe, the world|
Nima|b|Persian|Persian||just, fair-minded|Nima Yushij, father of modern Persian poetry
Pedram|b|Persian|Persian||happy, delightful|
Soroush|b|Persian|Avestan|Zoroastrian|obedience, divine hearing|Sraosha, Zoroastrian angel of obedience and messenger
Sohrab|b|Persian|Persian||red-faced, illustrious|son of Rostam, slain unknowingly by his father
Siavash|b|Persian|Avestan||owner of black stallions|innocent prince who passed through fire in the Shahnameh
Esfandiar|b|Persian|Avestan||created by the holy one|invulnerable prince who fought Rostam in the Shahnameh
Bahman|b|Persian|Avestan|Zoroastrian|good mind|Vohu Manah, Zoroastrian spirit of good thought
Kourosh|b|Persian|Old Persian||sun, like the sun|Cyrus the Great, founder of the Achaemenid Empire
Dariush|b|Persian|Old Persian||he who holds firm the good|Darius the Great, builder of Persepolis
Ardeshir|b|Persian|Middle Persian||ruling by truth|Ardashir I, founder of the Sasanian Empire
Khashayar|b|Persian|Old Persian||ruler of heroes|Xerxes the Great, Achaemenid king
Khosrow|b|Persian|Avestan||of good fame|Khosrow Anushirvan, celebrated Sasanian king
Kasra|b|Persian|Persian||of good fame|Arabic form of Khosrow, Sasanian king
Anoushiravan|b|Persian|Middle Persian||of immortal soul|Khosrow I Anushirvan, the Just
Kiumars|b|Persian|Avestan|Zoroastrian|mortal life|Gayomart, the first man and first king of the Shahnameh
Nariman|b|Persian|Avestan||manly, heroic-minded|ancestor of Rostam in the Shahnameh
Zal|b|Persian|Persian||white-haired|father of Rostam, raised by the Simorgh
Parviz|b|Persian|Persian||victorious|Khosrow Parviz, Sasanian king and lover of Shirin
Roozbeh|b|Persian|Persian||of good days, fortunate|the Persian birth name of Salman the Persian
Shahriar|b|Persian|Persian||king, sovereign|king of the Thousand and One Nights
Shapour|b|Persian|Middle Persian||son of the king|Shapur I, Sasanian king who defeated Rome
Shahrokh|b|Persian|Persian||royal-faced|
Teymour|b|Persian|Turkic||iron|
Yazdan|b|Persian|Persian|Zoroastrian|God, the divine|
Zartosht|b|Persian|Avestan|Zoroastrian|owner of old camels|Zarathustra, prophet of Zoroastrianism
Sepanta|b|Persian|Avestan|Zoroastrian|holy, sacred|
Hirbod|b|Persian|Middle Persian|Zoroastrian|Zoroastrian priest|
Hormoz|b|Persian|Avestan|Zoroastrian|wise lord (Ahura Mazda)|name of Sasanian kings and of the Strait of Hormuz
Mehr|e|Persian|Avestan|Zoroastrian|love, sun, covenant|Mehregan, the autumn festival of Mithra
Fariborz|b|Persian|Persian||of glorious stature|hero of the Shahnameh, son of Kay Kavus
Eskandar|b|Persian|Greek||defender of men|Alexander the Great, as he appears in the Shahnameh
Farhang|b|Persian|Persian||culture, learning|
Farshid|b|Persian|Persian||glorious light|
Farrokh|b|Persian|Persian||fortunate, auspicious|
Firouz|b|Persian|Persian||victorious|
Hooman|b|Persian|Persian||good-hearted|
Houshmand|b|Persian|Persian||intelligent, wise|
Sepehr|b|Persian|Persian||sky, the heavens|
Shayan|b|Persian|Persian||worthy, deserving|
Yashar|b|Persian|Turkic||may he live long|
Bahador|b|Persian|Turkic||brave, valiant|
Bamdad|b|Persian|Persian||dawn, early morning|
Francesco|b|Italian|Italian|Christian|frenchman, free one|Saint Francis of Assisi, patron saint of Italy
Tommaso|b|Italian|Aramaic|Christian|twin|Saint Thomas Aquinas
Edoardo|b|Italian|Germanic||wealthy guardian|
Mattia|b|Italian|Hebrew|Christian|gift of God|Saint Matthias the Apostle
Gabriele|b|Italian|Hebrew|Christian|God is my strength|the Archangel Gabriel; poet Gabriele D'Annunzio
Riccardo|b|Italian|Germanic||brave ruler|
Andrea|b|Italian|Greek|Christian|manly, brave|Saint Andrew; tenor Andrea Bocelli; a boy's name in Italy
Pietro|b|Italian|Greek|Christian|rock|Saint Peter
Nicolò|b|Italian|Greek|Christian|victory of the people|violinist Niccolò Paganini
Federico|b|Italian|Germanic||peaceful ruler|filmmaker Federico Fellini
Giuseppe|b|Italian|Hebrew|Christian|God will add|Giuseppe Verdi; Giuseppe Garibaldi
Antonio|b|Italian|Latin|Christian|of the Roman Antonius family|Saint Anthony of Padua; composer Antonio Vivaldi
Davide|b|Italian|Hebrew|Jewish,Christian|beloved|King David; Michelangelo's statue of David
Samuele|b|Italian|Hebrew||God has heard|
Giacomo|b|Italian|Hebrew|Christian|supplanter|composer Giacomo Puccini
Elia|b|Italian|Hebrew|Jewish,Christian|my God is Yahweh|the prophet Elijah
Michele|b|Italian|Hebrew|Christian|who is like God|the Archangel Michael
Luca|b|Italian|Latin|Christian|from Lucania|Saint Luke the Evangelist
Marco|b|Italian|Latin|Christian|dedicated to Mars|Saint Mark, patron of Venice; Marco Polo
Filippo|b|Italian|Greek|Christian|lover of horses|Saint Philip Neri
Alessio|b|Italian|Greek||defender|
Emanuele|b|Italian|Hebrew|Christian|God is with us|
Giorgio|b|Italian|Greek|Christian|farmer|Saint George; designer Giorgio Armani
Enea|b|Italian|Greek||praise|Aeneas, Trojan hero of Virgil's Aeneid
Jacopo|b|Italian|Hebrew||supplanter|painter Jacopo Tintoretto
Valerio|b|Italian|Latin||to be strong|
Simone|b|Italian|Hebrew|Christian|he has heard|
Daniele|b|Italian|Hebrew||God is my judge|
Stefano|b|Italian|Greek|Christian|crown|Saint Stephen, the first martyr
Vincenzo|b|Italian|Latin|Christian|conquering|
Salvatore|b|Italian|Latin|Christian|savior|honors Christ the Savior; common in the south
Raffaele|b|Italian|Hebrew|Christian|God heals|the Archangel Raphael
Raffaello|b|Italian|Hebrew|Christian|God heals|Renaissance painter Raffaello Sanzio
Cesare|b|Italian|Latin||from the Roman Caesar family|
Ettore|b|Italian|Greek||holding fast, steadfast|Hector, hero of Troy
Gioele|b|Italian|Hebrew|Jewish,Christian|Yahweh is God|the prophet Joel
Massimo|b|Italian|Latin||greatest|
Massimiliano|b|Italian|Latin||greatest|
Damiano|b|Italian|Greek|Christian|to tame|Saint Damian, physician martyr
Cristiano|b|Italian|Latin|Christian|follower of Christ|
Brando|b|Italian|Germanic||sword|
Ludovico|b|Italian|Germanic||famous warrior|poet Ludovico Ariosto
Leone|b|Italian|Latin||lion|
Paolo|b|Italian|Latin|Christian|small, humble|Saint Paul
Luigi|b|Italian|Germanic||famous warrior|playwright Luigi Pirandello
Carlo|b|Italian|Germanic||free man|
Mario|b|Italian|Latin||of the Roman Marius family|
Fabio|b|Italian|Latin||bean grower|
Fabrizio|b|Italian|Latin||craftsman|
Maurizio|b|Italian|Latin||Moorish, dark-skinned|
Nicola|b|Italian|Greek|Christian|victory of the people|Saint Nicholas, buried in Bari
Emilio|b|Italian|Latin||rival, eager|
Enrico|b|Italian|Germanic||ruler of the home|tenor Enrico Caruso; physicist Enrico Fermi
Elio|b|Italian|Greek||sun|
Ruggero|b|Italian|Germanic||famous spear|
Teodoro|b|Italian|Greek||gift of God|
Lucio|b|Italian|Latin||light|
Ottavio|b|Italian|Latin||eighth|
Vittorio|b|Italian|Latin||victor|filmmaker Vittorio De Sica
Gennaro|b|Italian|Latin|Christian|of January|San Gennaro, patron saint of Naples
Pasquale|b|Italian|Hebrew|Christian|of Easter, Passover|
Domenico|b|Italian|Latin|Christian|of the Lord|Saint Dominic
Ignazio|b|Italian|Latin|Christian|fiery|Saint Ignatius of Loyola
Rocco|b|Italian|Germanic|Christian|rest|Saint Roch, protector against plague
Santo|b|Italian|Latin|Christian|holy, saint|
Carmine|b|Italian|Hebrew|Christian|garden, orchard|Our Lady of Mount Carmel
Calogero|b|Italian|Greek|Christian|beautiful elder|Saint Calogerus, venerated in Sicily
Gaetano|b|Italian|Latin|Christian|from Gaeta|Saint Cajetan; composer Gaetano Donizetti
Nunzio|b|Italian|Latin|Christian|messenger, announcement|the Annunciation
Corrado|b|Italian|Germanic||bold counsel|
Bartolomeo|b|Italian|Aramaic|Christian|son of Talmai|Saint Bartholomew the Apostle
Benedetto|b|Italian|Latin|Christian|blessed|Saint Benedict of Norcia, patron of Europe
Cosimo|b|Italian|Greek|Christian|order, beauty|Cosimo de' Medici
Felice|b|Italian|Latin||happy, lucky|
Ferdinando|b|Italian|Germanic||bold voyager|
Fortunato|b|Italian|Latin||fortunate|
Gerardo|b|Italian|Germanic||brave spear|
Girolamo|b|Italian|Greek|Christian|sacred name|Saint Jerome
Guglielmo|b|Italian|Germanic||resolute protector|radio pioneer Guglielmo Marconi
Lino|b|Italian|Greek|Christian|flax|Pope Saint Linus
Marcello|b|Italian|Latin||young warrior|actor Marcello Mastroianni
Mauro|b|Italian|Latin||Moor, dark-skinned|
Nazzareno|b|Italian|Hebrew|Christian|from Nazareth|
Patrizio|b|Italian|Latin||nobleman|
Pio|b|Italian|Latin|Christian|pious|Padre Pio of Pietrelcina
Primo|b|Italian|Latin||first|writer Primo Levi
Renato|b|Italian|Latin|Christian|reborn|
Romeo|b|Italian|Italian||pilgrim to Rome|Shakespeare's Romeo of Verona
Sandro|b|Italian|Greek||defender of men|painter Sandro Botticelli
Sebastiano|b|Italian|Greek|Christian|venerable|Saint Sebastian
Severino|b|Italian|Latin||stern, serious|
Ugo|b|Italian|Germanic||mind, spirit|poet Ugo Foscolo
Vito|b|Italian|Latin|Christian|life|Saint Vitus
Agostino|b|Italian|Latin|Christian|venerable, great|Saint Augustine
Aldo|b|Italian|Germanic||old, noble|
Amedeo|b|Italian|Latin||loves God|painter Amedeo Modigliani
Angelo|b|Italian|Greek|Christian|messenger, angel|
Battista|b|Italian|Greek|Christian|baptizer|Saint John the Baptist
Biagio|b|Italian|Latin|Christian|lisping|Saint Blaise
Celestino|b|Italian|Latin|Christian|heavenly|
Cristoforo|b|Italian|Greek|Christian|bearer of Christ|Cristoforo Colombo
Donato|b|Italian|Latin|Christian|given|sculptor Donatello was Donato di Niccolò
Fiorenzo|b|Italian|Latin||flourishing|
Natale|b|Italian|Latin|Christian|Christmas, birth|
Piero|b|Italian|Greek||rock|painter Piero della Francesca
Sabino|b|Italian|Latin||Sabine man|
Saverio|b|Italian|Basque|Christian|new house|Saint Francis Xavier
Silvestro|b|Italian|Latin|Christian|of the woods|Pope Saint Sylvester
Tancredi|b|Italian|Germanic||thoughtful counsel|Tancredi, hero of the First Crusade
Timoteo|b|Italian|Greek|Christian|honoring God|
Zeno|b|Italian|Greek|Christian|of Zeus|Saint Zeno, patron of Verona
Alfredo|b|Italian|Germanic||elf counsel|
Armando|b|Italian|Germanic||army man|
Aurelio|b|Italian|Latin||golden|
Costantino|b|Italian|Latin||steadfast, constant|
Gioacchino|b|Italian|Hebrew|Christian|raised by God|composer Gioachino Rossini
Oreste|b|Italian|Greek||of the mountains|
Raimondo|b|Italian|Germanic||wise protector|
Rodolfo|b|Italian|Germanic||famous wolf|
Adriano|b|Italian|Latin||from Hadria|Emperor Hadrian; singer Adriano Celentano
Lamberto|b|Italian|Germanic||bright land|
Arnaldo|b|Italian|Germanic||eagle power|
Gualtiero|b|Italian|Germanic||army ruler|
Leopoldo|b|Italian|Germanic||bold people|
Adolfo|b|Italian|Germanic||noble wolf|
Alfonso|b|Italian|Germanic||noble and ready|
Ambrogio|b|Italian|Greek|Christian|immortal|Saint Ambrose, patron of Milan
Anselmo|b|Italian|Germanic|Christian|God helmet|Saint Anselm of Aosta
Benvenuto|b|Italian|Italian||welcome|goldsmith Benvenuto Cellini
Bonaventura|b|Italian|Italian|Christian|good fortune|Saint Bonaventure
Graziano|b|Italian|Latin||grace|
Marino|b|Italian|Latin||of the sea|
Michelangelo|b|Italian|Italian|Christian|Michael the angel|Michelangelo Buonarroti
Giordano|b|Italian|Hebrew||to descend, the Jordan|philosopher Giordano Bruno
Flavio|b|Italian|Latin||golden-haired|
Tobia|b|Italian|Hebrew|Christian|God is good|
Zaccaria|b|Italian|Hebrew|Christian|God remembers|
Giulio|b|Italian|Latin||of the Roman Julius family|
Gianluca|b|Italian|Italian||God is gracious, from Lucania|blend of Gianni and Luca
Ginevra|g|Italian|Welsh||fair and smooth|Leonardo's portrait Ginevra de' Benci
Vittoria|g|Italian|Latin||victory|
Beatrice|g|Italian|Latin||she who brings happiness|Dante's beloved Beatrice
Alice|g|Italian|Germanic||noble kind|
Ludovica|g|Italian|Germanic||famous warrior|
Camilla|g|Italian|Latin||young ritual attendant|warrior maiden Camilla in Virgil's Aeneid
Giorgia|g|Italian|Greek||farmer|
Nicole|g|Italian|Greek||victory of the people|
Gaia|g|Italian|Greek||earth|
Azzurra|g|Italian|Italian||sky blue|
Arianna|g|Italian|Greek||most holy|Ariadne of Greek myth
Adele|g|Italian|Germanic||noble|
Viola|g|Italian|Latin||violet|
Cecilia|g|Italian|Latin|Christian|blind|Saint Cecilia, patroness of music
Rachele|g|Italian|Hebrew||ewe|
Margherita|g|Italian|Greek||pearl|Queen Margherita, namesake of the pizza
Maria|g|Italian|Hebrew|Christian|beloved, or bitter|the Virgin Mary
Elisabetta|g|Italian|Hebrew|Christian|God is my oath|
Caterina|g|Italian|Greek|Christian|pure|Saint Catherine of Siena, patroness of Italy
Benedetta|g|Italian|Latin|Christian|blessed|
Ottavia|g|Italian|Latin||eighth|
Agnese|g|Italian|Greek|Christian|pure, chaste|Saint Agnes
Angelica|g|Italian|Greek||angelic|
Allegra|g|Italian|Italian||cheerful, lively|
Carlotta|g|Italian|Germanic||free woman|
Costanza|g|Italian|Latin||constancy|
Diana|g|Italian|Latin||divine|the Roman goddess of the hunt
Fiamma|g|Italian|Italian||flame|
Flavia|g|Italian|Latin||golden-haired|
Gemma|g|Italian|Italian|Christian|gem|Saint Gemma Galgani of Lucca
Ilaria|g|Italian|Latin||cheerful|
Lucrezia|g|Italian|Latin||profit, wealth|Lucrezia Borgia
Serena|g|Italian|Latin||calm, serene|
Silvia|g|Italian|Latin||of the forest|
Sveva|g|Italian|Germanic||woman from Swabia|
Veronica|g|Italian|Greek|Christian|bringer of victory|Saint Veronica
Alessia|g|Italian|Greek||defender|
Alessandra|g|Italian|Greek||defender of men|
Michela|g|Italian|Hebrew||who is like God|
Federica|g|Italian|Germanic||peaceful ruler|
Roberta|g|Italian|Germanic||bright fame|
Paola|g|Italian|Latin||small, humble|
Simona|g|Italian|Hebrew||she has heard|
Simonetta|g|Italian|Hebrew||she has heard|Simonetta Vespucci, Botticelli's muse
Stefania|g|Italian|Greek||crown|
Raffaella|g|Italian|Hebrew||God heals|
Emanuela|g|Italian|Hebrew||God is with us|
Gabriella|g|Italian|Hebrew||God is my strength|
Donatella|g|Italian|Latin||given|designer Donatella Versace
Graziella|g|Italian|Latin||grace|
Grazia|g|Italian|Latin|Christian|grace|
Concetta|g|Italian|Latin|Christian|conception|the Immaculate Conception
Assunta|g|Italian|Latin|Christian|taken up|the Assumption of Mary
Carmela|g|Italian|Hebrew|Christian|garden, orchard|Our Lady of Mount Carmel
Rosalia|g|Italian|Latin|Christian|rose|Saint Rosalia, patroness of Palermo
Annunziata|g|Italian|Latin|Christian|announced|the Annunciation
Immacolata|g|Italian|Latin|Christian|immaculate|the Immaculate Conception
Addolorata|g|Italian|Italian|Christian|sorrowful|Our Lady of Sorrows
Rosaria|g|Italian|Latin|Christian|rosary|Our Lady of the Rosary
Filomena|g|Italian|Greek|Christian|friend of strength|Saint Philomena
Giuseppina|g|Italian|Hebrew|Christian|God will add|
Nunzia|g|Italian|Latin|Christian|announcement|the Annunciation
Santa|g|Italian|Latin|Christian|holy, saint|
Maddalena|g|Italian|Hebrew|Christian|woman of Magdala|Saint Mary Magdalene
Agata|g|Italian|Greek|Christian|good|Saint Agatha, patroness of Catania
Alba|g|Italian|Latin||dawn|
Amalia|g|Italian|Germanic||work|
Amelia|g|Italian|Germanic||work|
Annalisa|g|Italian|Hebrew||grace, God is my oath|
Delia|g|Italian|Greek||from Delos|
Domenica|g|Italian|Latin|Christian|of the Lord, Sunday|
Enrica|g|Italian|Germanic||ruler of the home|
Fabiola|g|Italian|Latin||bean grower|
Fiore|g|Italian|Italian||flower|
Franca|g|Italian|Germanic||free|
Ida|g|Italian|Germanic||work|
Letizia|g|Italian|Latin||joy, happiness|
Liliana|g|Italian|Latin||lily|
Luisa|g|Italian|Germanic||famous warrior|
Marcella|g|Italian|Latin||young warrior|
Mirella|g|Italian|Occitan||admired|
Patrizia|g|Italian|Latin||noblewoman|
Piera|g|Italian|Greek||rock|
Rossella|g|Italian|Italian||red|Italian name for Scarlett O'Hara
Sabina|g|Italian|Latin||Sabine woman|
Susanna|g|Italian|Hebrew||lily|
Virginia|g|Italian|Latin||maiden|
Viviana|g|Italian|Latin||alive|
Zita|g|Italian|Italian|Christian|little girl|Saint Zita of Lucca
Perla|g|Italian|Italian||pearl|
Stella|g|Italian|Latin||star|
Nicoletta|g|Italian|Greek||victory of the people|
Giada|g|Italian|Italian||jade|
Melissa|g|Italian|Greek||honeybee|
Debora|g|Italian|Hebrew||bee|
Ester|g|Italian|Persian|Jewish|star|Queen Esther of the Purim story
Claudia|g|Italian|Latin||of the Roman Claudius family|actress Claudia Cardinale
Giovanna|g|Italian|Hebrew|Christian|God is gracious|
Lorenza|g|Italian|Latin||from Laurentum|
Adriana|g|Italian|Latin||from Hadria|
Vincenza|g|Italian|Latin|Christian|conquering|
Elettra|g|Italian|Greek||amber, shining|
Ambra|g|Italian|Italian||amber|
Dafne|g|Italian|Greek||laurel|
Gioia|g|Italian|Italian||joy|
Speranza|g|Italian|Italian||hope|
Marina|g|Italian|Latin||of the sea|
Orsola|g|Italian|Latin|Christian|little bear|Saint Ursula
Teodora|g|Italian|Greek||gift of God|
Maura|g|Italian|Latin||Moorish, dark-skinned|
Ortensia|g|Italian|Latin||gardener|
Sibilla|g|Italian|Greek||prophetess|
Antonietta|g|Italian|Latin||of the Roman Antonius family|
Lupita|g|Mexican|Arabic|Christian|valley of the wolf|pet form of Guadalupe
Fernando|b|Mexican|Germanic||bold voyager|Fernando Valenzuela
Regina|g|Mexican|Latin|Christian|queen|Mary as Queen of Heaven
Refugio|e|Mexican|Spanish|Christian|refuge|Our Lady Refuge of Sinners
Lola|g|Mexican|Spanish|Christian|sorrows|pet form of Dolores
Concepción|g|Mexican|Spanish|Christian|conception|the Immaculate Conception
Conchita|g|Mexican|Spanish|Christian|conception|pet form of Concepción
Paz|g|Mexican|Spanish|Christian|peace|Our Lady of Peace
Asunción|g|Mexican|Spanish|Christian|assumption|the Assumption of Mary
Araceli|g|Mexican|Latin|Christian|altar of heaven|
Montserrat|g|Mexican|Catalan|Christian|serrated mountain|Our Lady of Montserrat
Frida|g|Mexican|Germanic||peace|Frida Kahlo, painter
Patricia|g|Mexican|Latin||noble|
Rubí|g|Mexican|Spanish||ruby|
Azucena|g|Mexican|Arabic||white lily|
Isabel|g|Mexican|Hebrew|Christian|pledged to God|
Alondra|g|Mexican|Spanish||lark|
Margarita|g|Mexican|Greek||pearl|
Carlota|g|Mexican|Germanic||free woman|Empress Carlota of Mexico
Cielo|g|Mexican|Spanish||sky, heaven|
Yazmín|g|Mexican|Persian||jasmine|
Pancho|b|Mexican|Latin|Christian|Frenchman|pet form of Francisco; Pancho Villa
Guillermo|b|Mexican|Germanic||resolute protector|Guillermo del Toro, filmmaker
Vicente|b|Mexican|Latin|Christian|conquering|Vicente Guerrero, hero of independence
Porfirio|b|Mexican|Greek||purple|Porfirio Díaz, president
Venustiano|b|Mexican|Latin||of Venus|Venustiano Carranza, president
Iker|b|Mexican|Basque|Christian|visitation|
Octavio|b|Mexican|Latin||eighth|Octavio Paz, Nobel laureate poet
Cristóbal|b|Mexican|Greek|Christian|bearer of Christ|
Hugo|b|Mexican|Germanic||mind, spirit|
Rogelio|b|Mexican|Germanic||famous spear|
Jacinto|b|Mexican|Greek||hyacinth|
Isidro|b|Mexican|Greek|Christian|gift of Isis|Saint Isidore the Farmer, patron of farmers
Cruz|e|Mexican|Spanish|Christian|cross|
Trinidad|e|Mexican|Spanish|Christian|trinity|
Natividad|e|Mexican|Spanish|Christian|nativity|
Xóchitl|g|Nahua|Nahuatl||flower|
Citlali|g|Nahua|Nahuatl||star|
Quetzalli|g|Nahua|Nahuatl||precious feather|
Tonatiuh|b|Nahua|Nahuatl||sun|the Aztec sun god
Cuauhtémoc|b|Nahua|Nahuatl||descending eagle|last Aztec emperor
Moctezuma|b|Nahua|Nahuatl||he who frowns like a lord|Aztec emperor
Nezahualcóyotl|b|Nahua|Nahuatl||fasting coyote|poet-king of Texcoco
Tenoch|b|Nahua|Nahuatl||stone prickly pear|legendary founder of Tenochtitlan
Coatl|b|Nahua|Nahuatl||serpent|
Metztli|e|Nahua|Nahuatl||moon|
Ehécatl|b|Nahua|Nahuatl||wind|the Aztec wind god
Tlali|e|Nahua|Nahuatl||earth|
Xochiquetzal|g|Nahua|Nahuatl||flower feather|Aztec goddess of beauty and love
Tonantzin|g|Nahua|Nahuatl||our revered mother|mother goddess, linked to the Virgin of Guadalupe
Itzcóatl|b|Nahua|Nahuatl||obsidian serpent|Aztec ruler
Cuauhtli|b|Nahua|Nahuatl||eagle|
Ollin|e|Nahua|Nahuatl||movement|
Mazatl|b|Nahua|Nahuatl||deer|
Yolotl|e|Nahua|Nahuatl||heart|
Yolotzin|g|Nahua|Nahuatl||little heart|
Ameyalli|g|Nahua|Nahuatl||spring, fountain|
Atl|b|Nahua|Nahuatl||water|
Yaotl|b|Nahua|Nahuatl||warrior|
Yoloxóchitl|g|Nahua|Nahuatl||heart flower|the Mexican magnolia
Tonalli|e|Nahua|Nahuatl||warmth of the sun|
Axayácatl|b|Nahua|Nahuatl||water face|Aztec ruler
Ahuízotl|b|Nahua|Nahuatl||water creature|Aztec ruler
Malinalli|g|Nahua|Nahuatl||twisted grass|birth name of La Malinche
Huitzilin|b|Nahua|Nahuatl||hummingbird|
Ocelotl|b|Nahua|Nahuatl||jaguar|
Itzli|b|Nahua|Nahuatl||obsidian|
Chimalli|b|Nahua|Nahuatl||shield|
Mixtli|e|Nahua|Nahuatl||cloud|
Quiahuitl|e|Nahua|Nahuatl||rain|
Xochipilli|b|Nahua|Nahuatl||flower prince|Aztec god of art, music and flowers
Chalchihuitl|e|Nahua|Nahuatl||jade, precious stone|
Xihuitl|e|Nahua|Nahuatl||turquoise; year|
Cuicatl|e|Nahua|Nahuatl||song|
Acamapichtli|b|Nahua|Nahuatl||handful of reeds|first ruler of Tenochtitlan
Chimalpopoca|b|Nahua|Nahuatl||smoking shield|Aztec ruler
Huitzilíhuitl|b|Nahua|Nahuatl||hummingbird feather|Aztec ruler
Itzel|g|Maya|Yucatec Maya||lady rainbow|form of Ixchel
Ixchel|g|Maya|Yucatec Maya||lady rainbow|Maya goddess of the moon and childbirth
Nicte|g|Maya|Yucatec Maya||flower|
Sac-Nicté|g|Maya|Yucatec Maya||white flower|princess of Mayapán in Maya legend
Kukulkán|b|Maya|Yucatec Maya||feathered serpent|serpent deity of Chichén Itzá
Balam|b|Maya|Yucatec Maya||jaguar|
Zazil|g|Maya|Yucatec Maya||light, brightness|
Kin|b|Maya|Yucatec Maya||sun, day|
Ek|e|Maya|Yucatec Maya||star|
Ik|b|Maya|Yucatec Maya||wind|
Pakal|b|Maya|Yucatec Maya||shield|K'inich Janaab Pakal, king of Palenque
Eréndira|g|Purépecha|Purépecha||smiling one|Purépecha princess who resisted the Spanish
Erandi|g|Purépecha|Purépecha||dawn|
Tzitziki|g|Purépecha|Purépecha||flower|
Tariácuri|b|Purépecha|Purépecha||priest of the wind|founder of the Purépecha state
Nayeli|g|Zapotec|Zapotec||I love you|
Donají|g|Zapotec|Zapotec||great soul|Zapotec princess of Oaxaca legend
Enkhjargal|g|Mongolian|Mongolian||peaceful happiness|
Bolormaa|g|Mongolian|Mongolian||crystal (with the feminine suffix -maa)|
Oyunchimeg|g|Mongolian|Mongolian||ornament of wisdom|
Temuulen|g|Mongolian|Mongolian||aspiration, striving forward|Temülün, the only sister of Chinggis Khaan
Khulan|g|Mongolian|Mongolian||wild horse, onager|Khulan Khatun, a wife of Chinggis Khaan
Saruul|e|Mongolian|Mongolian||bright, clear|
Nomin|g|Mongolian|Mongolian||lapis lazuli, deep blue|
Solongo|g|Mongolian|Mongolian||rainbow|
Tsetsegmaa|g|Mongolian|Mongolian||flower (with the feminine suffix -maa)|
Altantsetseg|g|Mongolian|Mongolian||golden flower|
Narantsetseg|g|Mongolian|Mongolian||sunflower, flower of the sun|
Sarangerel|g|Mongolian|Mongolian||moonlight|
Bat-Erdene|b|Mongolian|Mongolian||firm jewel|Bat-Erdene, celebrated Naadam wrestling champion
Batbayar|b|Mongolian|Mongolian||firm joy|
Ganbold|b|Mongolian|Mongolian||steel and steel, doubly strong|
Erdenebat|b|Mongolian|Mongolian||firm jewel|
Temujin|b|Mongolian|Mongolian||blacksmith, of iron|the birth name of Chinggis Khaan
Batzorig|b|Mongolian|Mongolian||firm courage|
Munkh-Erdene|b|Mongolian|Mongolian||eternal jewel|
Tumurbaatar|b|Mongolian|Mongolian||iron hero|
Sukhbaatar|b|Mongolian|Mongolian||axe hero|Damdin Sükhbaatar, hero of the 1921 revolution
Ganzorig|b|Mongolian|Mongolian||steel courage|
Khongorzul|g|Mongolian|Mongolian||tulip|
Ariunaa|g|Mongolian|Mongolian||pure, holy|
Uyanga|g|Mongolian|Mongolian||melody|
Misheel|g|Mongolian|Mongolian||smile|
Ochir|b|Mongolian|Sanskrit|Buddhist|vajra, thunderbolt|
Dorj|b|Mongolian|Tibetan|Buddhist|vajra, thunderbolt|
Enkhtuya|g|Mongolian|Mongolian||ray of peace|
Tuul|e|Mongolian|Mongolian||the Tuul River|the river that flows through Ulaanbaatar
Zaya|g|Mongolian|Mongolian||fate, destiny|
Bat|b|Mongolian|Mongolian||firm, strong|Batu Khan, founder of the Golden Horde
Erdene|e|Mongolian|Mongolian||jewel, treasure|
Bold|b|Mongolian|Mongolian||steel|
Tsetseg|g|Mongolian|Mongolian||flower|
Enkh|e|Mongolian|Mongolian||peace|
Bayar|b|Mongolian|Mongolian||joy|
Altan|b|Mongolian|Mongolian||golden|Altan Khan, 16th-century ruler who named the Dalai Lama
Saran|g|Mongolian|Mongolian||moon|
Naran|e|Mongolian|Mongolian||sun|
Oyun|g|Mongolian|Mongolian||mind, wisdom|
Tuya|g|Mongolian|Mongolian||ray of light|
Baatar|b|Mongolian|Mongolian||hero|
Tumur|b|Mongolian|Mongolian||iron|
Chuluun|b|Mongolian|Mongolian||stone|
Jargal|e|Mongolian|Mongolian||happiness|
Gerel|g|Mongolian|Mongolian||light|
Munkh|b|Mongolian|Mongolian||eternal|Möngke Khan, fourth Great Khan of the Mongol Empire
Bolor|g|Mongolian|Mongolian||crystal|
Borte|g|Mongolian|Mongolian||blue-grey|Börte, empress and first wife of Chinggis Khaan
Jochi|b|Mongolian|Mongolian||guest|eldest son of Chinggis Khaan
Tolui|b|Mongolian|Mongolian||mirror|youngest son of Chinggis Khaan
Mandukhai|g|Mongolian|Mongolian||one who rises|Mandukhai the Wise, queen who reunited the Mongols
Tsetsen|b|Mongolian|Mongolian||wise, eloquent|Tsetsen Khan, title of one of the four Khalkha khans
Tsolmon|e|Mongolian|Mongolian||morning star, Venus|
Sarnai|g|Mongolian|Mongolian||rose|
Odgerel|g|Mongolian|Mongolian||starlight|
Odbayar|b|Mongolian|Mongolian||star joy|
Odonchimeg|g|Mongolian|Mongolian||ornament of stars|
Odtsetseg|g|Mongolian|Mongolian||star flower|
Gerelmaa|g|Mongolian|Mongolian||light (with the feminine suffix -maa)|
Enkhbayar|b|Mongolian|Mongolian||peaceful joy|Nambaryn Enkhbayar, president of Mongolia 2005-2009
Enkhbold|b|Mongolian|Mongolian||peaceful steel|
Enkhsaikhan|b|Mongolian|Mongolian||peaceful and beautiful|
Enkhzaya|g|Mongolian|Mongolian||peaceful destiny|
Enkhtsetseg|g|Mongolian|Mongolian||flower of peace|
Elbegdorj|b|Mongolian|Mongolian|Buddhist|abundant vajra|Tsakhiagiin Elbegdorj, president of Mongolia 2009-2017
Battulga|b|Mongolian|Mongolian||firm hearth-support|Khaltmaagiin Battulga, president of Mongolia 2017-2021
Khurelsukh|b|Mongolian|Mongolian||bronze axe|Ukhnaagiin Khürelsükh, president of Mongolia from 2021
Batmunkh|b|Mongolian|Mongolian||firm and eternal|Jambyn Batmönkh, leader during the 1990 democratic transition
Batbold|b|Mongolian|Mongolian||firm steel|Sükhbaataryn Batbold, prime minister of Mongolia
Altankhuyag|b|Mongolian|Mongolian||golden armor|Norovyn Altankhuyag, prime minister of Mongolia
Oyun-Erdene|b|Mongolian|Mongolian||jewel of wisdom|Luvsannamsrain Oyun-Erdene, prime minister of Mongolia
Amarjargal|e|Mongolian|Mongolian||calm happiness|Rinchinnyamyn Amarjargal, prime minister of Mongolia
Amarsanaa|b|Mongolian|Mongolian||calm mind|Amursana, 18th-century Oirat prince
Ochirbat|b|Mongolian|Mongolian|Buddhist|firm vajra|Punsalmaagiin Ochirbat, first directly elected president
Natsagdorj|b|Mongolian|Tibetan|Buddhist|universal vajra|Dashdorjiin Natsagdorj, poet of "My Native Land"
Zanabazar|b|Mongolian|Sanskrit|Buddhist|wisdom vajra|Zanabazar, first Bogd Gegeen and master sculptor
Rinchen|b|Mongolian|Tibetan|Buddhist|precious jewel|Byambyn Rinchen, scholar and novelist
Sambuu|b|Mongolian|Tibetan|Buddhist|good, excellent|Jamsrangiin Sambuu, head of state 1954-1972
Lkhagva|e|Mongolian|Tibetan|Buddhist|Mercury, Wednesday|traditionally given to a child born on a Wednesday
Dolgor|g|Mongolian|Tibetan|Buddhist|White Tara|
Tsend|b|Mongolian|Tibetan|Buddhist|possessing long life|
Davaa|e|Mongolian|Tibetan|Buddhist|moon, Monday|traditionally given to a child born on a Monday
Myagmar|e|Mongolian|Tibetan|Buddhist|Mars, Tuesday|traditionally given to a child born on a Tuesday
Purev|e|Mongolian|Tibetan|Buddhist|Jupiter, Thursday|traditionally given to a child born on a Thursday
Baasan|e|Mongolian|Tibetan|Buddhist|Venus, Friday|traditionally given to a child born on a Friday
Byamba|e|Mongolian|Tibetan|Buddhist|Saturn, Saturday|traditionally given to a child born on a Saturday
Nyam|e|Mongolian|Tibetan|Buddhist|sun, Sunday|traditionally given to a child born on a Sunday
Nyamaa|g|Mongolian|Tibetan|Buddhist|sun, Sunday|
Dulmaa|g|Mongolian|Tibetan|Buddhist|Tara, the savioress|Tara, the female Buddha of compassion
Tseren|b|Mongolian|Tibetan|Buddhist|long life|
Tserendorj|b|Mongolian|Tibetan|Buddhist|long-life vajra|
Damdin|b|Mongolian|Tibetan|Buddhist|horse-necked one, Hayagriva|Damdin Sükhbaatar, revolutionary hero
Gombo|b|Mongolian|Tibetan|Buddhist|protector, Mahakala|
Gombodorj|b|Mongolian|Tibetan|Buddhist|protector vajra|
Jamyan|b|Mongolian|Tibetan|Buddhist|gentle voice, Manjushri|
Sodnom|b|Mongolian|Tibetan|Buddhist|merit|
Luvsan|b|Mongolian|Tibetan|Buddhist|good mind, noble intellect|
Namjil|b|Mongolian|Tibetan|Buddhist|completely victorious|
Galsan|b|Mongolian|Tibetan|Buddhist|good fortune|
Dondog|b|Mongolian|Tibetan|Buddhist|one who has accomplished his aim|
Badam|e|Mongolian|Sanskrit|Buddhist|lotus|
Badamtsetseg|g|Mongolian|Sanskrit|Buddhist|lotus flower|
Dash|b|Mongolian|Tibetan|Buddhist|auspicious|
Dashdorj|b|Mongolian|Tibetan|Buddhist|auspicious vajra|
Dashdondog|b|Mongolian|Tibetan|Buddhist|auspicious accomplishment|
Norov|b|Mongolian|Tibetan|Buddhist|jewel|
Dagva|b|Mongolian|Tibetan|Buddhist|pure|
Namsrai|b|Mongolian|Tibetan|Buddhist|Vaisravana, guardian of wealth|
Sanjaa|b|Mongolian|Tibetan|Buddhist|Buddha, the awakened one|
Puntsag|b|Mongolian|Tibetan|Buddhist|perfect, excellent|
Gonchig|b|Mongolian|Tibetan|Buddhist|rare and precious, the Three Jewels|
Khandmaa|g|Mongolian|Tibetan|Buddhist|dakini, sky-goer|
Khorloo|g|Mongolian|Tibetan|Buddhist|wheel|the Buddhist wheel of dharma
Odval|g|Mongolian|Sanskrit|Buddhist|blue lotus|
Ayush|b|Mongolian|Sanskrit|Buddhist|long life|
Batdorj|b|Mongolian|Mongolian|Buddhist|firm vajra|
Bat-Ochir|b|Mongolian|Mongolian|Buddhist|firm vajra|
Nergui|e|Mongolian|Mongolian||no name|a protective name meant to hide the child from evil spirits
Enebish|e|Mongolian|Mongolian||not this one|a protective name meant to confuse evil spirits
Terbish|e|Mongolian|Mongolian||not that one|a protective name meant to confuse evil spirits
Khunbish|b|Mongolian|Mongolian||not a human|a protective name meant to confuse evil spirits
Munkhbayar|b|Mongolian|Mongolian||eternal joy|
Munkhbat|b|Mongolian|Mongolian||eternally firm|
Munkhbold|b|Mongolian|Mongolian||eternal steel|
Munkhjargal|g|Mongolian|Mongolian||eternal happiness|
Munkhtsetseg|g|Mongolian|Mongolian||eternal flower|
Munkhtuya|g|Mongolian|Mongolian||eternal ray of light|
Munkhzul|g|Mongolian|Mongolian||eternal lamp|
Altangerel|e|Mongolian|Mongolian||golden light|
Altanchimeg|g|Mongolian|Mongolian||golden ornament|
Altanzaya|g|Mongolian|Mongolian||golden destiny|
Naranbaatar|b|Mongolian|Mongolian||sun hero|
Narangerel|g|Mongolian|Mongolian||sunlight|
Sarantuya|g|Mongolian|Mongolian||moonbeam|
Saranchimeg|g|Mongolian|Mongolian||ornament of the moon|
Tsogtbaatar|b|Mongolian|Mongolian||glorious hero|
Khurelbaatar|b|Mongolian|Mongolian||bronze hero|
Ganbaatar|b|Mongolian|Mongolian||steel hero|
Ganbat|b|Mongolian|Mongolian||firm steel|
Ganbayar|b|Mongolian|Mongolian||steel joy|
Ganerdene|b|Mongolian|Mongolian||steel jewel|
Gansukh|b|Mongolian|Mongolian||steel axe|
Gantulga|b|Mongolian|Mongolian||steel hearth-support|
Ganchuluun|b|Mongolian|Mongolian||steel stone|
Gantumur|b|Mongolian|Mongolian||steel and iron|
Batchuluun|b|Mongolian|Mongolian||firm stone|
Chuluunbaatar|b|Mongolian|Mongolian||stone hero|
Tumurchuluun|b|Mongolian|Mongolian||iron stone|
Tumurkhuyag|b|Mongolian|Mongolian||iron armor|
Batkhuyag|b|Mongolian|Mongolian||firm armor|
Erdenekhuyag|b|Mongolian|Mongolian||jewel armor|
Battumur|b|Mongolian|Mongolian||firm iron|
Batsukh|b|Mongolian|Mongolian||firm axe|
Batsaikhan|b|Mongolian|Mongolian||firm and beautiful|
Batjargal|b|Mongolian|Mongolian||firm happiness|
Batsuuri|b|Mongolian|Mongolian||firm foundation|
Battsetseg|g|Mongolian|Mongolian||firm flower|
Bayarmaa|g|Mongolian|Mongolian||joy (with the feminine suffix -maa)|
Bayarsaikhan|b|Mongolian|Mongolian||joyful and beautiful|
Bayartsetseg|g|Mongolian|Mongolian||flower of joy|
Bayarjargal|e|Mongolian|Mongolian||joy and happiness|
Bayarkhuu|b|Mongolian|Mongolian||joyful boy|
Bayasgalan|b|Mongolian|Mongolian||joy, delight|
Erdenechimeg|g|Mongolian|Mongolian||jewel ornament|
Erdenetsetseg|g|Mongolian|Mongolian||jewel flower|
Erdenetuya|g|Mongolian|Mongolian||jewel ray|
Erdenebileg|b|Mongolian|Mongolian||jewel of wisdom|
Oyuntsetseg|g|Mongolian|Mongolian||flower of wisdom|
Oyunbileg|g|Mongolian|Mongolian||wisdom and talent|
Oyunsuvd|g|Mongolian|Mongolian||pearl of wisdom|
Suvd|g|Mongolian|Mongolian||pearl|
Bolortsetseg|g|Mongolian|Mongolian||crystal flower|
Bolorerdene|g|Mongolian|Mongolian||crystal jewel|
Bolorchimeg|g|Mongolian|Mongolian||crystal ornament|
Munguntsetseg|g|Mongolian|Mongolian||silver flower|
Gerelchimeg|g|Mongolian|Mongolian||ornament of light|
Delger|e|Mongolian|Mongolian||abundant, flourishing|
Delgermaa|g|Mongolian|Mongolian||abundant (with the feminine suffix -maa)|
Javkhlan|b|Mongolian|Mongolian||glorious, splendid|
Khishig|e|Mongolian|Mongolian||blessing, grace|
Bilguun|b|Mongolian|Mongolian||wise|
Bilegt|b|Mongolian|Mongolian||gifted, wise|
Tengis|b|Mongolian|Mongolian||sea|
Ankhbayar|b|Mongolian|Mongolian||first joy|
Ankhtsetseg|g|Mongolian|Mongolian||first flower|
Uuganbayar|b|Mongolian|Mongolian||first-born joy|
Uugantsetseg|g|Mongolian|Mongolian||first-born flower|
Saikhan|e|Mongolian|Mongolian||beautiful|
Undrakh|e|Mongolian|Mongolian||to sprout, spring forth|
Khatanbaatar|b|Mongolian|Mongolian||steadfast hero|Khatanbaatar Magsarjav, general of the 1921 revolution
Arslan|b|Mongolian|Turkic||lion|
Erkhem|b|Mongolian|Mongolian||noble, honored|
Erkhembayar|b|Mongolian|Mongolian||noble joy|
Ider|b|Mongolian|Mongolian||vigorous, youthful|
Tugsjargal|g|Mongolian|Mongolian||complete happiness|
Tugsbayar|b|Mongolian|Mongolian||complete joy|
Tuguldur|b|Mongolian|Mongolian||complete, perfect|
Nasanjargal|g|Mongolian|Mongolian||happy life|
Jargalsaikhan|b|Mongolian|Mongolian||beautiful happiness|
Odkhuu|b|Mongolian|Mongolian||star boy|
Gankhuu|b|Mongolian|Mongolian||steel boy|
Ariunzaya|g|Mongolian|Mongolian||pure destiny|
Ariunbold|b|Mongolian|Mongolian||pure steel|
Shijir|e|Mongolian|Mongolian||pure gold|
Khasbaatar|b|Mongolian|Mongolian||jade hero|
Tamir|b|Mongolian|Mongolian||strength, vigor|
Unenbat|b|Mongolian|Mongolian||firm truth|
Sansar|b|Mongolian|Sanskrit||universe, cosmos|
Mergen|b|Mongolian|Mongolian||wise, skilled marksman|
Sergelen|b|Mongolian|Mongolian||lively, alert|
Khuslen|g|Mongolian|Mongolian||wish, desire|
Enerel|g|Mongolian|Mongolian||compassion, mercy|
Tuyaa|g|Mongolian|Mongolian||ray of light|
Naraa|g|Mongolian|Mongolian||sun|
Saraa|g|Mongolian|Mongolian||moon|
Gerelt|e|Mongolian|Mongolian||radiant, full of light|
Altantuya|g|Mongolian|Mongolian||golden ray|
Naranchimeg|g|Mongolian|Mongolian||ornament of the sun|
Sarantsetseg|g|Mongolian|Mongolian||moon flower|
Odontuya|g|Mongolian|Mongolian||ray of starlight|
Oyungerel|g|Mongolian|Mongolian||light of wisdom|
Enkhchimeg|g|Mongolian|Mongolian||ornament of peace|
Delgertsetseg|g|Mongolian|Mongolian||abundant flower|
Jargalmaa|g|Mongolian|Mongolian||happiness (with the feminine suffix -maa)|
Bolorsuvd|g|Mongolian|Mongolian||crystal pearl|
Munkhchimeg|g|Mongolian|Mongolian||eternal ornament|
Erdenesuvd|g|Mongolian|Mongolian||jewel pearl|
Gerelsuvd|g|Mongolian|Mongolian||pearl of light|
Álvaro|b|Spanish|Germanic||guardian of all|
Leo|b|Spanish|Latin||lion|
Izan|b|Spanish|Hebrew||firm, strong|Spanish form of Ethan, a hit in Spain since the 2000s
Gonzalo|b|Spanish|Germanic||battle genius|
Sergio|b|Spanish|Latin|Christian|of the Roman Sergius family|Saint Sergius
Unai|b|Spanish|Basque||cowherd|
Aitor|b|Spanish|Basque||good father|legendary forefather of the Basque people
Asier|b|Spanish|Basque||the beginning|
Ander|b|Spanish|Basque|Christian|manly, brave|Basque form of Andrés
Julen|b|Spanish|Latin||youthful|Basque form of Julián
Ibai|b|Spanish|Basque||river|
Víctor|b|Spanish|Latin||conqueror|
Jaime|b|Spanish|Hebrew|Christian|supplanter|James I the Conqueror, King of Aragon
Alonso|b|Spanish|Germanic||noble and ready|Alonso Quijano, the real name of Don Quixote
Julio|b|Spanish|Latin||of the Roman Julius family|
Fermín|b|Spanish|Latin|Christian|firm, steady|Saint Fermin, honored at the Sanfermines in Pamplona
Isidoro|b|Spanish|Greek|Christian|gift of Isis|Saint Isidore of Seville
Pelayo|b|Spanish|Greek||of the sea|Pelagius, first king of Asturias
Sancho|b|Spanish|Latin||sanctified, holy|Sancho Panza in Don Quixote
Baltasar|b|Spanish|Akkadian|Christian|God protect the king|one of the Three Kings
Melchor|b|Spanish|Hebrew|Christian|king of light|one of the Three Kings
Marcelo|b|Spanish|Latin||little warrior of Mars|
Adán|b|Spanish|Hebrew|Christian,Jewish|man, of the earth|
Saúl|b|Spanish|Hebrew|Christian,Jewish|asked for|first king of Israel
Cayetano|b|Spanish|Latin|Christian|from Gaeta|Saint Cajetan
Borja|b|Spanish|Arabic||tower|from the town of Borja; Saint Francis Borgia
Moisés|b|Spanish|Hebrew|Jewish,Christian|drawn out of the water|
Jonás|b|Spanish|Hebrew|Christian,Jewish|dove|the prophet Jonah
Eloy|b|Spanish|Latin|Christian|chosen|Saint Eligius
Hilario|b|Spanish|Latin||cheerful|
Inocencio|b|Spanish|Latin|Christian|innocent|
Marcial|b|Spanish|Latin||of Mars, martial|
Narciso|b|Spanish|Greek||daffodil|
Plácido|b|Spanish|Latin||calm, peaceful|Plácido Domingo, tenor
Prudencio|b|Spanish|Latin||prudent, wise|
Urbano|b|Spanish|Latin||of the city|
Amador|b|Spanish|Latin||lover|
Clemente|b|Spanish|Latin||merciful|
Constantino|b|Spanish|Latin||steadfast|
Pascual|b|Spanish|Hebrew|Christian|of Easter, Passover|
Román|b|Spanish|Latin||Roman|
Mauricio|b|Spanish|Latin||dark-skinned, Moorish|
Bernabé|b|Spanish|Aramaic|Christian|son of consolation|Saint Barnabas
Benigno|b|Spanish|Latin||kind|
Feliciano|b|Spanish|Latin||happy, lucky|
Cipriano|b|Spanish|Greek||from Cyprus|
Ildefonso|b|Spanish|Germanic|Christian|ready for battle|Saint Ildefonsus of Toledo
Eusebio|b|Spanish|Greek||pious|
Joel|b|Spanish|Hebrew|Jewish,Christian|Yahweh is God|the prophet Joel
Iñaki|b|Basque|Latin|Christian|fiery|Basque form of Ignacio
Xabier|b|Basque|Basque|Christian|new house|Saint Francis Xavier
Mikel|b|Basque|Hebrew|Christian|who is like God?|Basque form of Miguel
Gorka|b|Basque|Greek|Christian|farmer|Basque form of Jorge
Joseba|b|Basque|Hebrew|Christian|God will add|Basque form of José
Jon|b|Basque|Hebrew|Christian|God is gracious|Basque form of Juan
Markel|b|Basque|Latin||of Mars, warlike|Basque form of Marcos
Hodei|b|Basque|Basque||cloud|
Gaizka|b|Basque|Basque|Christian|savior|Basque form of Salvador
Jordi|b|Catalan|Greek|Christian|farmer|Sant Jordi, patron of Catalonia
Pau|b|Catalan|Latin|Christian|small, humble|Pau Casals, cellist; also means peace in Catalan
Arnau|b|Catalan|Germanic||eagle power|
Pol|b|Catalan|Latin||small, humble|
Oriol|b|Catalan|Latin||golden|
Jaume|b|Catalan|Hebrew|Christian|supplanter|
Josep|b|Catalan|Hebrew|Christian|God will add|
Martí|b|Catalan|Latin||of Mars|
Pere|b|Catalan|Greek|Christian|rock, stone|
Ferran|b|Catalan|Germanic||bold voyager|
Joan|b|Catalan|Hebrew|Christian|God is gracious|Joan Miró, painter
Jan|b|Catalan|Hebrew||God is gracious|
Biel|b|Catalan|Hebrew|Christian|God is my strength|Catalan short form of Gabriel
Aleix|b|Catalan|Greek||defender|
Nil|b|Catalan|Greek||the Nile river|
Marc|b|Catalan|Latin||of Mars, warlike|
Xoán|b|Galician|Hebrew|Christian|God is gracious|
Brais|b|Galician|Latin|Christian|lisping|Galician form of Blas
Iago|b|Galician|Hebrew|Christian|supplanter|Galician form of James
Xián|b|Galician|Latin||youthful|Galician form of Julián
Xurxo|b|Galician|Greek|Christian|farmer|Galician form of Jorge
Martiño|b|Galician|Latin||of Mars|
Carla|g|Spanish|Germanic||free woman|
Vega|g|Spanish|Spanish||fertile meadow|also the bright star Vega
Candelaria|g|Spanish|Latin|Christian|Candlemas|Our Lady of Candelaria, patroness of the Canary Islands
Macarena|g|Spanish|Greek|Christian|blessed|Our Lady of Hope of Macarena, Seville
Inmaculada|g|Spanish|Latin|Christian|immaculate|the Immaculate Conception of Mary
Begoña|g|Spanish|Basque|Christian|place of the dominant hill|Our Lady of Begoña, patroness of Biscay
Covadonga|g|Spanish|Latin|Christian|cave of the Lady|Our Lady of Covadonga, patroness of Asturias
Almudena|g|Spanish|Arabic|Christian|the citadel|Our Lady of La Almudena, patroness of Madrid
Nieves|g|Spanish|Spanish|Christian|snows|Our Lady of the Snows
Encarnación|g|Spanish|Latin|Christian|incarnation|the Incarnation of Christ
Fuensanta|g|Spanish|Spanish|Christian|holy fountain|Our Lady of Fuensanta, patroness of Murcia
Reyes|g|Spanish|Spanish|Christian|kings|Our Lady of the Kings, patroness of Seville
Angustias|g|Spanish|Latin|Christian|anguish, sorrows|Our Lady of Sorrows, patroness of Granada
Loreto|g|Spanish|Latin|Christian|laurel grove|Our Lady of Loreto
Sagrario|g|Spanish|Latin|Christian|tabernacle, sanctuary|Our Lady of the Sagrario, patroness of Toledo
Camino|g|Spanish|Spanish|Christian|the way|Our Lady of the Way, patroness of León
Henar|g|Spanish|Spanish|Christian|hayfield|Our Lady of El Henar, patroness of Segovia's farmers
Gracia|g|Spanish|Latin|Christian|grace|Our Lady of Grace
Estrella|g|Spanish|Latin|Christian|star|Mary as Star of the Sea
Purificación|g|Spanish|Latin|Christian|purification|the Purification of Mary
Pastora|g|Spanish|Latin|Christian|shepherdess|the Divine Shepherdess of Seville
Mar|g|Spanish|Latin|Christian|sea|short for María del Mar, Our Lady of the Sea
Aránzazu|g|Spanish|Basque|Christian|among the hawthorns|Our Lady of Aránzazu, patroness of Gipuzkoa
Arantxa|g|Spanish|Basque|Christian|hawthorn|Arantxa Sánchez Vicario, tennis champion
Beatriz|g|Spanish|Latin||she who brings joy|
Lorena|g|Spanish|French||from Lorraine|
Blanca|g|Spanish|Germanic||white|Blanche of Castile
Ariadna|g|Spanish|Greek||most holy|
Lidia|g|Spanish|Greek||woman from Lydia|
Nerea|g|Spanish|Greek||sea nymph|
Jara|g|Spanish|Spanish||rockrose|
Azahara|g|Spanish|Arabic||orange blossom|Medina Azahara, the palace-city near Córdoba
Rebeca|g|Spanish|Hebrew|Jewish,Christian|to bind, captivating|wife of Isaac
Judit|g|Spanish|Hebrew|Jewish,Christian|woman of Judea|
Eulalia|g|Spanish|Greek|Christian|well-spoken|Saint Eulalia of Mérida
Águeda|g|Spanish|Greek|Christian|good|Saint Agatha
Flor|g|Spanish|Latin||flower|
Alejandra|g|Spanish|Greek||defender of the people|
Francisca|g|Spanish|Latin|Christian|Frenchwoman, free one|
Antonia|g|Spanish|Latin||of the Roman Antonius family|
Rafaela|g|Spanish|Hebrew|Christian|God heals|
Gema|g|Spanish|Latin||gem|
Estefanía|g|Spanish|Greek||crown|
Cayetana|g|Spanish|Latin||from Gaeta|Cayetana Fitz-James Stuart, Duchess of Alba
Berta|g|Spanish|Germanic||bright|
Amaia|g|Spanish|Basque||the end|
Ainara|g|Spanish|Basque||swallow|
Nahia|g|Spanish|Basque||desire, wish|
Edurne|g|Basque|Basque|Christian|snow|Basque form of Nieves
Zuriñe|g|Basque|Basque||white|
Lorea|g|Basque|Basque||flower|
Garazi|g|Basque|Latin|Christian|grace|Basque form of Engracia
Uxue|g|Basque|Basque|Christian|dove|Our Lady of Ujué, Navarre
Laia|g|Catalan|Greek|Christian|well-spoken|Catalan short form of Eulàlia, patroness of Barcelona
Aina|g|Catalan|Hebrew||grace|Catalan form of Ana
Mercè|g|Catalan|Latin|Christian|mercy|Our Lady of Mercy, patroness of Barcelona
Roser|g|Catalan|Latin|Christian|rosary|
Jana|g|Catalan|Hebrew||God is gracious|
Ona|g|Catalan|Catalan||wave|
Uxía|g|Galician|Greek|Christian|well-born|Galician form of Eugenia
Sabela|g|Galician|Hebrew|Christian|God is my oath|Galician form of Isabel
Iria|g|Galician|Greek|Christian|peace|Saint Iria, Galician form of Irene
Awadia|g|Sudanese|Arabic||compensation, recompense|
Amna|g|Sudanese|Arabic||safe, secure|
Mawahib|g|Sudanese|Arabic||gifts, talents|
Muna|g|Sudanese|Arabic||wishes, desires|
Rabab|g|Sudanese|Arabic||white cloud|
Sawsan|g|Sudanese|Arabic||lily|
Hiba|g|Sudanese|Arabic||gift|
Ikhlas|g|Sudanese|Arabic|Islamic|sincerity, pure devotion|Surat al-Ikhlas of the Quran
Ishraga|g|Sudanese|Arabic||radiance, sunrise|Sudanese spelling of Ishraqa
Igbal|g|Sudanese|Arabic||prosperity, good fortune|Sudanese spelling of Iqbal
Afaf|g|Sudanese|Arabic||chastity, virtue|
Wigdan|g|Sudanese|Arabic||conscience, deep feeling|Sudanese spelling of Wijdan
Sumaya|g|Sudanese|Arabic|Islamic|high, lofty|Sumayya, the first martyr of Islam
Suad|g|Sudanese|Arabic||happiness|
Najwa|g|Sudanese|Arabic||confidential talk, secret|
Nawal|g|Sudanese|Arabic||gift, bounty|
Salwa|g|Sudanese|Arabic||solace, comfort|
Thuraya|g|Sudanese|Arabic||the Pleiades|
Widad|g|Sudanese|Arabic||love, affection|
Wisal|g|Sudanese|Arabic||union, reunion|
Hanan|g|Sudanese|Arabic||tenderness, compassion|
Insaf|g|Sudanese|Arabic||fairness, justice|
Intisar|g|Sudanese|Arabic||victory|
Manal|g|Sudanese|Arabic||attainment|
Nada|g|Sudanese|Arabic||dew; generosity|
Nour|e|Sudanese|Arabic||light|
Rasha|g|Sudanese|Arabic||young gazelle|
Reem|g|Sudanese|Arabic||white gazelle|
Shadia|g|Sudanese|Arabic||singer, melodious|
Tahani|g|Sudanese|Arabic||congratulations|
Tagwa|g|Sudanese|Arabic|Islamic|piety, God-consciousness|Sudanese spelling of Taqwa
Wafa|g|Sudanese|Arabic||loyalty, faithfulness|
Azza|g|Sudanese|Arabic||might, glory|"Azza fi Hawak", patriotic song in which Azza stands for Sudan
Rawda|g|Sudanese|Arabic||garden, meadow|
Batool|g|Sudanese|Arabic|Islamic|ascetic, devoted to God|a title of Fatima, daughter of the Prophet
Ilham|g|Sudanese|Arabic||inspiration|
Inaam|g|Sudanese|Arabic||bounty, favor|
Ihsan|e|Sudanese|Arabic|Islamic|excellence, beneficence|
Nagla|g|Sudanese|Arabic||wide-eyed|Sudanese spelling of Najla
Nimat|g|Sudanese|Arabic||blessings|
Hikma|g|Sudanese|Arabic||wisdom|
Kawthar|g|Sudanese|Arabic|Islamic|abundance|al-Kawthar, a river in paradise in the Quran
Fathia|g|Sudanese|Arabic||victorious, opener|
Bakhita|g|Sudanese|Arabic|Christian|fortunate, lucky|St. Josephine Bakhita, Sudanese-born saint
Mastoura|g|Sudanese|Arabic||sheltered, protected|
Gisma|g|Sudanese|Arabic||destiny, one's portion|Sudanese spelling of Qisma
Hamda|g|Sudanese|Arabic||praise|
Mahasin|g|Sudanese|Arabic||virtues, good qualities|
Durra|g|Sudanese|Arabic||pearl|
Lubna|g|Sudanese|Arabic||storax tree|
Shaza|g|Sudanese|Arabic||fragrance|
Duaa|g|Sudanese|Arabic|Islamic|prayer, supplication|
Alaa|e|Sudanese|Arabic||nobility, excellence|
Hala|g|Sudanese|Arabic||halo around the moon|
Maha|g|Sudanese|Arabic||oryx|
Nisreen|g|Sudanese|Persian||wild rose|
Mariam|g|Sudanese|Hebrew|Islamic,Christian|beloved; wished-for child|Mary, mother of Jesus
Osman|b|Sudanese|Arabic|Islamic|young bustard|Osman Digna, Mahdist commander from eastern Sudan
Bashir|b|Sudanese|Arabic||bringer of good news|
Tayeb|b|Sudanese|Arabic||good, kind|Tayeb Salih, Sudanese novelist
Babiker|b|Sudanese|Arabic|Islamic|father of the young camel|Sudanese form of Abu Bakr
Elfatih|b|Sudanese|Arabic||the conqueror, the opener|
Elnour|b|Sudanese|Arabic||the light|
Mahjoub|b|Sudanese|Arabic||veiled, protected|
Yousif|b|Sudanese|Hebrew|Islamic|God will increase|Sudanese spelling of Yusuf (Joseph)
Gaafar|b|Sudanese|Arabic||stream, rivulet|Gaafar Nimeiry, Sudanese president
Hamad|b|Sudanese|Arabic||praised|
Omer|b|Sudanese|Arabic|Islamic|flourishing, long-lived|Umar ibn al-Khattab, second caliph
Suleiman|b|Sudanese|Hebrew|Islamic|peaceful|the prophet-king Solomon
Abdalla|b|Sudanese|Arabic|Islamic|servant of God|Abdallahi ibn Muhammad, the Mahdi's successor
Abdelrahman|b|Sudanese|Arabic|Islamic|servant of the Most Merciful|
Mubarak|b|Sudanese|Arabic||blessed|
Salih|b|Sudanese|Arabic|Islamic|righteous|the prophet Salih
Siddig|b|Sudanese|Arabic|Islamic|truthful|Sudanese spelling of Siddiq, title of Abu Bakr
Hashim|b|Sudanese|Arabic|Islamic|crusher of bread|Hashim, great-grandfather of the Prophet
Anwar|b|Sudanese|Arabic||more luminous|
Fadul|b|Sudanese|Arabic||grace, favor|Sudanese form of Fadl
Gamal|b|Sudanese|Arabic||beauty|Sudanese and Egyptian form of Jamal
Mohanad|b|Sudanese|Arabic||sword of Indian steel|
Mudathir|b|Sudanese|Arabic|Islamic|the cloaked one|Surat al-Muddaththir of the Quran
Muzamil|b|Sudanese|Arabic|Islamic|the wrapped one|Surat al-Muzzammil of the Quran
Obeid|b|Sudanese|Arabic||little servant (of God)|
Sami|b|Sudanese|Arabic||elevated, sublime|
Seif|b|Sudanese|Arabic||sword|
Waleed|b|Sudanese|Arabic||newborn|
Yasir|b|Sudanese|Arabic||easy, prosperous|
Ammar|b|Sudanese|Arabic|Islamic|long-lived|Ammar ibn Yasir, companion of the Prophet
Hatim|b|Sudanese|Arabic||decisive judge|Hatim al-Tai, legendary for generosity
Ayman|b|Sudanese|Arabic||fortunate, blessed|
Imad|b|Sudanese|Arabic||pillar, support|
Isam|b|Sudanese|Arabic||safeguard, protection|
Sharif|b|Sudanese|Arabic||noble, honorable|
Hisham|b|Sudanese|Arabic||generosity|
Ziyad|b|Sudanese|Arabic||growth, abundance|
Awad|b|Sudanese|Arabic||compensation, reward|
Kheiri|b|Sudanese|Arabic||good, charitable|
Mutasim|b|Sudanese|Arabic||one who holds fast to God|
Deng|b|South Sudanese|Dinka||rain; the sky divinity|Luol Deng, South Sudanese-British basketball player
Garang|b|South Sudanese|Dinka||the first man in Dinka myth|John Garang, founder of the SPLM
Abuk|g|South Sudanese|Dinka||the first woman in Dinka myth|Dinka goddess of women and gardens
Akol|b|South Sudanese|Dinka||sun, daytime|
Mabior|b|South Sudanese|Dinka||white ox|
Malual|b|South Sudanese|Dinka||reddish-brown ox|
Makuei|b|South Sudanese|Dinka||ox with fish-eagle coloring|
Nyandeng|g|South Sudanese|Dinka||daughter of Deng|Rebecca Nyandeng de Mabior, South Sudanese politician
Kiir|b|South Sudanese|Dinka||river, the Nile|Salva Kiir, first president of South Sudan
Thon|b|South Sudanese|Dinka||bull, male|Thon Maker, basketball player
Nhial|b|South Sudanese|Dinka||sky, above|
Bol|b|South Sudanese|Dinka||child born after twins|Manute Bol, basketball player
Gatluak|b|South Sudanese|Nuer||son of the cattle byre|
Nyaluak|g|South Sudanese|Nuer||daughter of the cattle byre|
Gatwech|b|South Sudanese|Nuer||son of the cattle camp|
Nyawech|g|South Sudanese|Nuer||daughter of the cattle camp|
Gatkuoth|b|South Sudanese|Nuer||son of God|
Nyakuoth|g|South Sudanese|Nuer||daughter of God|
Gatmal|b|South Sudanese|Nuer||son of peace|
Nyamal|g|South Sudanese|Nuer||daughter of peace|
Nyagoa|g|South Sudanese|Nuer||good, beautiful daughter|
Kandake|g|Nubian|Meroitic||queen mother|title of the ruling queens of ancient Kush
Candace|g|Nubian|Meroitic||queen mother|Greco-Roman form of Kandake, title of Kushite queens
Kashta|b|Nubian|Meroitic||the Kushite|Kashta, Kushite king who began the conquest of Egypt
Amanirenas|g|Nubian|Meroitic||name honoring the god Amun|one-eyed Kushite queen who fought Rome
Amanishakheto|g|Nubian|Meroitic||name honoring the god Amun|Kushite queen famed for her gold jewelry
Amanitore|g|Nubian|Meroitic||name honoring the god Amun|Kushite queen who built temples at Naqa
Arkamani|b|Nubian|Meroitic||name honoring the god Amun|Arkamani I (Ergamenes), king of Meroe
Kyriakos|b|Nubian|Greek|Christian|of the lord|Kyriakos, Christian king of Makuria
Merkurios|b|Nubian|Latin|Christian|of Mercury|Merkurios, Makurian king called the New Constantine
Shahzoda|g|Uzbek|Persian||princess|
Zarina|g|Uzbek|Persian||golden|
Madina|g|Uzbek|Arabic|Islamic|city|named for Medina, the city of the Prophet
Kamola|g|Uzbek|Arabic||perfection|
Nigora|g|Uzbek|Persian||beloved, sweetheart|
Feruza|g|Uzbek|Persian||turquoise|the blue tiles of Samarkand's domes
Shoira|g|Uzbek|Arabic||poetess|
Sitora|g|Uzbek|Persian||star|
Mohira|g|Uzbek|Arabic||skillful|
Dilfuza|g|Uzbek|Persian||one who delights the heart|
Nilufar|g|Uzbek|Persian||water lily|
Barno|g|Uzbek|Persian||young and graceful|
Sarvinoz|g|Uzbek|Persian||graceful cypress|
Mohinur|g|Uzbek|Persian||moonlight|
Robiya|g|Uzbek|Arabic|Islamic|fourth|Rabia al-Adawiyya, the Sufi saint of Basra
Dilorom|g|Uzbek|Persian||comfort of the heart|
Dildora|g|Uzbek|Persian||beloved|
Gulbahor|g|Uzbek|Persian||spring flower|
Muhabbat|g|Uzbek|Arabic||love|
Mahliyo|g|Uzbek|Persian||moon-like beauty|
Mohlaroyim|g|Uzbek|Persian||moon-like lady|birth name of the poet Nodira
Oysha|g|Uzbek|Arabic|Islamic|alive, living|Aisha, wife of the Prophet Muhammad
Fotima|g|Uzbek|Arabic|Islamic|one who abstains|Fatima, daughter of the Prophet Muhammad
Xadicha|g|Uzbek|Arabic|Islamic|early-born child|Khadija, first wife of the Prophet Muhammad
Zuhra|g|Uzbek|Arabic||Venus, radiance|
Zulfiya|g|Uzbek|Persian||curly-haired|Zulfiya Isroilova, beloved Uzbek poet
Saodat|g|Uzbek|Arabic||happiness|
Nasiba|g|Uzbek|Arabic||of noble descent|
Nargiza|g|Uzbek|Persian||narcissus flower|
Rayhona|g|Uzbek|Arabic||sweet basil|
Gavhar|g|Uzbek|Persian||jewel, pearl|
Durdona|g|Uzbek|Persian||a single precious pearl|
Marjona|g|Uzbek|Arabic||pearls, coral|
Munisa|g|Uzbek|Arabic||friendly companion|
Muxlisa|g|Uzbek|Arabic||sincere, devoted|
Latofat|g|Uzbek|Arabic||grace, elegance|
Komila|g|Uzbek|Arabic||perfect|
Hilola|g|Uzbek|Arabic||crescent moon|
Iroda|g|Uzbek|Arabic||willpower, determination|
Laylo|g|Uzbek|Arabic||night|Layli and Majnun, retold by Alisher Navoi
Mavluda|g|Uzbek|Arabic||newborn|
Muattar|g|Uzbek|Arabic||fragrant|
Mushtariy|g|Uzbek|Arabic||the planet Jupiter|
Parizod|g|Uzbek|Persian||born of a fairy|
Parvina|g|Uzbek|Persian||the Pleiades|
Ruxsora|g|Uzbek|Persian||fair-cheeked|
Sayyora|g|Uzbek|Arabic||planet|
Shahnoza|g|Uzbek|Persian||darling of the king|
Shohista|g|Uzbek|Persian||worthy, deserving|
Umida|g|Uzbek|Persian||hope|
Vazira|g|Uzbek|Arabic||minister, counselor|
Zebo|g|Uzbek|Persian||beautiful|
Ziyoda|g|Uzbek|Arabic||abundance|
Zilola|g|Uzbek|Persian||pure clear water|
Gulnoza|g|Uzbek|Persian||delicate flower|
Gulruh|g|Uzbek|Persian||flower-faced|
Dilnura|g|Uzbek|Persian||light of the heart|
Oygul|g|Uzbek|Turkic||moon flower|
Oltinoy|g|Uzbek|Turkic||golden moon|
Kumush|g|Uzbek|Turkic||silver|heroine of Abdulla Qodiriy's novel Days Gone By
Nozanin|g|Uzbek|Persian||delicate, graceful|
Ozoda|g|Uzbek|Persian||free|
Sanobar|g|Uzbek|Persian||pine tree|
Sohiba|g|Uzbek|Arabic||companion|
Xurshida|g|Uzbek|Persian||sun|
Aziza|g|Uzbek|Arabic||precious, dear|
Dilafruz|g|Uzbek|Persian||heart-brightening|
Mahbuba|g|Uzbek|Arabic||beloved|
Marhabo|g|Uzbek|Arabic||welcome|
Navbahor|g|Uzbek|Persian||early spring|
Rano|g|Uzbek|Persian||beautiful, graceful|
Sabohat|g|Uzbek|Arabic||beauty, fairness|
Sevinch|g|Uzbek|Turkic||joy|
Shodiya|g|Uzbek|Persian||joy|
Tursunoy|g|Uzbek|Turkic||may she stay, moon|
Yasmina|g|Uzbek|Persian||jasmine|
Zamira|g|Uzbek|Arabic||conscience, inner heart|
Mehribon|g|Uzbek|Persian||kind, affectionate|
Hulkar|g|Uzbek|Turkic||the Pleiades|
Ulfat|g|Uzbek|Arabic||friendship, closeness|
Nazokat|g|Uzbek|Persian||delicacy, grace|
Bahora|g|Uzbek|Persian||spring|
Gulandom|g|Uzbek|Persian||graceful as a flower|
Mohichehra|g|Uzbek|Persian||moon-faced|
Muslima|g|Uzbek|Arabic|Islamic|Muslim woman|
Dinora|g|Uzbek|Arabic||gold coin|
Gulsanam|g|Uzbek|Persian||beauty like a flower|
Jasur|b|Uzbek|Arabic||brave, bold|
Sardor|b|Uzbek|Persian||chief, leader|
Bekzod|b|Uzbek|Turkic||born of a lord, noble-born|
Bobur|b|Uzbek|Persian||tiger|Babur, founder of the Mughal Empire, born in Andijan
Temur|b|Uzbek|Turkic||iron|Amir Temur, conqueror who made Samarkand his capital
Ulugbek|b|Uzbek|Turkic||great lord|Ulugbek, astronomer-king who built Samarkand's observatory
Alisher|b|Uzbek|Persian||lion Ali|Alisher Navoi, father of Uzbek literature
Otabek|b|Uzbek|Turkic||fatherly lord|hero of Abdulla Qodiriy's novel Days Gone By
Doniyor|b|Uzbek|Hebrew|Islamic|God is my judge|the prophet Daniel
Farrux|b|Uzbek|Persian||happy, fortunate|
Jahongir|b|Uzbek|Persian||world conqueror|Jahangir, Mughal emperor and descendant of Babur
Akmal|b|Uzbek|Arabic||most perfect|
Shavkat|b|Uzbek|Arabic||might, glory|
Sherzod|b|Uzbek|Persian||born of a lion|
Ilhom|b|Uzbek|Arabic||inspiration|
Azamat|b|Uzbek|Arabic||greatness, grandeur|
Dilshod|b|Uzbek|Persian||happy-hearted|
Islom|b|Uzbek|Arabic|Islamic|submission to God|
Asadbek|b|Uzbek|Arabic||lion lord|
Abdulaziz|b|Uzbek|Arabic|Islamic|servant of the Almighty|
Abdulla|b|Uzbek|Arabic|Islamic|servant of God|Abdulla Qodiriy, author of the first Uzbek novel
Abdurahmon|b|Uzbek|Arabic|Islamic|servant of the Most Merciful|
Abdurashid|b|Uzbek|Arabic|Islamic|servant of the Rightly Guiding|
Abdusalom|b|Uzbek|Arabic|Islamic|servant of the Source of Peace|
Abdumalik|b|Uzbek|Arabic|Islamic|servant of the King|
Mustafo|b|Uzbek|Arabic|Islamic|the chosen one|an epithet of the Prophet Muhammad
Ibrohim|b|Uzbek|Hebrew|Islamic|father of multitudes|the prophet Abraham
Ismoil|b|Uzbek|Hebrew|Islamic|God hears|the prophet Ishmael
Iso|b|Uzbek|Hebrew|Islamic|God is salvation|the prophet Jesus
Muso|b|Uzbek|Hebrew|Islamic|drawn out of the water|the prophet Moses
Yoqub|b|Uzbek|Hebrew|Islamic|supplanter|the prophet Jacob
Sulaymon|b|Uzbek|Hebrew|Islamic|peace|the prophet Solomon
Dovud|b|Uzbek|Hebrew|Islamic|beloved|the prophet David
Yahyo|b|Uzbek|Hebrew|Islamic|God is gracious|the prophet John the Baptist
Odil|b|Uzbek|Arabic||just, fair|
Usmon|b|Uzbek|Arabic|Islamic|young bustard|Uthman, the third caliph
Husayn|b|Uzbek|Arabic|Islamic|little good one|Husayn, grandson of the Prophet
Husan|b|Uzbek|Arabic||beauty|
Bahodir|b|Uzbek|Turkic||brave hero|
Botir|b|Uzbek|Turkic||brave, hero|
Anvar|b|Uzbek|Arabic||most radiant|
Bahrom|b|Uzbek|Persian||victorious|
Elbek|b|Uzbek|Turkic||lord of the people|
Erkin|b|Uzbek|Turkic||free|
Fazliddin|b|Uzbek|Arabic|Islamic|grace of the faith|
Ikrom|b|Uzbek|Arabic||honor, generosity|
Iskandar|b|Uzbek|Greek||defender of men|Alexander the Great, who took Samarkand (Marakanda)
Jaloliddin|b|Uzbek|Arabic|Islamic|majesty of the faith|Jalal ad-Din Mingburnu, Khwarazmian sultan
Kamoliddin|b|Uzbek|Arabic|Islamic|perfection of the faith|
Shamsiddin|b|Uzbek|Arabic|Islamic|sun of the faith|
Nuriddin|b|Uzbek|Arabic|Islamic|light of the faith|
Najmiddin|b|Uzbek|Arabic|Islamic|star of the faith|
Sirojiddin|b|Uzbek|Arabic|Islamic|lamp of the faith|
Zayniddin|b|Uzbek|Arabic|Islamic|ornament of the faith|
Baxtiyor|b|Uzbek|Persian||fortunate, lucky|
Laziz|b|Uzbek|Arabic||delightful, pleasant|
Mirzo|b|Uzbek|Persian||prince|
Murod|b|Uzbek|Arabic||wish, desire|
Nodir|b|Uzbek|Arabic||rare|
Nurbek|b|Uzbek|Arabic||lord of light|
Obid|b|Uzbek|Arabic||worshipper|
Oybek|b|Uzbek|Turkic||moon lord|Oybek, celebrated Uzbek poet and novelist
Orif|b|Uzbek|Arabic||knowing, wise|
Pulat|b|Uzbek|Persian||steel|
Qodir|b|Uzbek|Arabic||powerful|
Ravshan|b|Uzbek|Persian||bright, clear|
Ruslan|b|Uzbek|Turkic||lion|
Shuhrat|b|Uzbek|Arabic||fame|
Sobir|b|Uzbek|Arabic||patient|
Sodiq|b|Uzbek|Arabic||truthful|
Tohir|b|Uzbek|Arabic||pure|Tohir and Zuhra, a classic Uzbek love legend
Tolib|b|Uzbek|Arabic||seeker|
Ulmas|b|Uzbek|Turkic||immortal|
Umid|b|Uzbek|Persian||hope|
Vali|b|Uzbek|Arabic||friend, guardian|
Xurshid|b|Uzbek|Persian||sun|
Zafar|b|Uzbek|Arabic||victory|
Zokir|b|Uzbek|Arabic|Islamic|one who remembers God|
Humoyun|b|Uzbek|Persian||fortunate, royal|Humayun, Mughal emperor and son of Babur
Komil|b|Uzbek|Arabic||perfect|
Kamron|b|Uzbek|Persian||successful|
Lutfulla|b|Uzbek|Arabic|Islamic|kindness of God|
Rauf|b|Uzbek|Arabic||compassionate|
Said|b|Uzbek|Arabic||happy, fortunate|
Tursun|b|Uzbek|Turkic||may he stay|
Tolqin|b|Uzbek|Turkic||wave|
Abbos|b|Uzbek|Arabic|Islamic|stern, austere|Abbas, uncle of the Prophet Muhammad
Bilol|b|Uzbek|Arabic|Islamic|moisture, water|Bilal, the first muezzin of Islam
Bunyod|b|Uzbek|Persian||foundation|
Diyor|b|Uzbek|Persian||land, country|
Eldor|b|Uzbek|Turkic||ruler of the land|
Elyor|b|Uzbek|Turkic||friend of the people|
Izzat|b|Uzbek|Arabic||honor, glory|
Javohir|b|Uzbek|Arabic||jewels|
Kamol|b|Uzbek|Arabic||perfection|
Mubin|b|Uzbek|Arabic||clear, evident|
Muzaffar|b|Uzbek|Arabic||victorious|
Navruz|b|Uzbek|Persian||new day|the spring New Year festival
Qahramon|b|Uzbek|Persian||hero|
Shahzod|b|Uzbek|Persian||prince, born of a king|
Sunnat|b|Uzbek|Arabic|Islamic|the Prophet's tradition|
Zohid|b|Uzbek|Arabic||ascetic, pious|
Abror|b|Uzbek|Arabic||the righteous|
Asror|b|Uzbek|Arabic||secrets|
Davlat|b|Uzbek|Arabic||wealth, fortune|
Fayzulla|b|Uzbek|Arabic|Islamic|bounty of God|Fayzulla Xo'jayev, Bukhara statesman
Hikmat|b|Uzbek|Arabic||wisdom|
Sarvar|b|Uzbek|Persian||leader, chief|
Behzod|b|Uzbek|Persian||well-born|Kamoliddin Behzod, master miniature painter of Herat
Firdavs|b|Uzbek|Persian||paradise|
Ozod|b|Uzbek|Persian||free|
Suhani|g|Hindi|Hindi||pleasant, beautiful, charming|Written सुहानी, the feminine of the Hindi word सुहाना (suhānā): pleasant, agreeable, and, as a verb, to seem attractive or to be an adornment. It comes from Sanskrit शुभान (śubhāná). (Wiktionary, after McGregor’s Oxford Hindi–English Dictionary)
Nupur|g|Hindi|Hindi||anklet|Written नूपुर, from Sanskrit नूपुर (nūpura): an ornament for the toes or ankles, an anklet, a word used in the Mahabharata and classical poetry. (Monier-Williams Sanskrit–English Dictionary)
Kapil|b|Hindi|Hindi|Hindu|tawny, reddish-brown|Written कपिल, from Sanskrit कपिल (kapila): brown, tawny, reddish. Also the name of an ancient sage, identified by some with Vishnu and held to be the founder of the Sāṃkhya school of philosophy (Mahabharata, Bhagavad Gita). (Monier-Williams Sanskrit–English Dictionary)
Sonal|g|Indian|Hindi||gold, golden|Written सोनल. From Hindi सोना (sonā), Marathi सोन (son) or Gujarati સોનું (sonũ), “gold”, all from Sanskrit सुवर्ण (suvarṇa), literally “good colour”. (Behind the Name; Wiktionary)
Ariana|g|Greek|Greek||most holy|A modern form of Ariadne: Cretan Greek ari “most” + adnos “holy”. Ariadne was the Cretan princess who gave Theseus the thread that led him out of the Labyrinth. (Wiktionary; Behind the Name)
Saroj|e|Indian|Sanskrit||lotus|Written सरोज, from Sanskrit सरोज (saroja), “produced or found in lakes”, and so a lotus: saras “lake” + ja “born”. (Monier-Williams Sanskrit–English Dictionary)
Aishwarya|g|Indian|Sanskrit|Hindu|prosperity, power|Written ऐश्वर्या, from Sanskrit ऐश्वर्य (aiśvarya): the state of being a mighty lord, sovereignty, power, and so prosperity. (Monier-Williams Sanskrit–English Dictionary)
`;

const REAL = REAL_RAW.trim().split("\n").map(line => {
  const [n, g, o, l, r, m, src] = line.split("|");
  return { n, g: { g: "girl", b: "boy", e: "either" }[g], o, l, r: r ? r.split(",") : [], m, src, type: "real" };
});
