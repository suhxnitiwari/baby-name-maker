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
`;

const REAL = REAL_RAW.trim().split("\n").map(line => {
  const [n, g, o, l, r, m, src] = line.split("|");
  return { n, g: { g: "girl", b: "boy", e: "either" }[g], o, l, r: r ? r.split(",") : [], m, src, type: "real" };
});
