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
Maya|g|Indian|Sanskrit|Buddhist,Hindu|illusion, magic|mother of the Buddha
Rahul|b|Indian|Sanskrit|Buddhist||son of the Buddha
Sujata|g|Indian|Sanskrit|Buddhist|well-born|offered rice to the Buddha before his enlightenment
Yashodhara|g|Indian|Sanskrit|Buddhist|bearer of glory|wife of the Buddha
Dharma|e|Indian|Sanskrit|Hindu,Buddhist|duty, cosmic law|
Mahavir|b|Indian|Sanskrit|Jain|great hero|24th Tirthankara of Jainism
Rishabh|b|Indian|Sanskrit|Jain|best, excellent|first Tirthankara of Jainism
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
`;

const REAL = REAL_RAW.trim().split("\n").map(line => {
  const [n, g, o, l, r, m, src] = line.split("|");
  return { n, g: { g: "girl", b: "boy", e: "either" }[g], o, l, r: r ? r.split(",") : [], m, src, type: "real" };
});
