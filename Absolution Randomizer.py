import xml.etree.ElementTree as ET
import random
import os.path
from itertools import chain

def randomize_classes(lord: bool, thieves: bool, dancer: bool, prologueCrew: bool, balanced: bool, usefulThings, units_file, units):
    '''This function randomly assigns tier 1 classes to the specified units.'''
    unchangedUnits = usefulThings['unchangedUnits']
    #For now, we'll just create a list of base classes, and we'll figure out promotions
    #and other stuff later.
    class_list = usefulThings['unpromotedClasses']
    #Remove things not randomized from the randomization list
    if not lord:
        class_list.remove('Adelita')
        unchangedUnits.append("Valentina")
    if not thieves:
        class_list.remove('Thief')
        class_list.remove('Spy')
        unchangedUnits += ["Quentin", "Yewande", "Raul"]
    if not dancer:
        class_list.remove('Dancer')
        unchangedUnits.append("Nadia")
    if not prologueCrew:
        unchangedUnits += ["ValentinaY", "Jeremy", "Raul", "Cesar"]
    class_copy = [item for item in class_list]
    #We make this copy so that if there's a balanced class distribution, we don't run out of classes before units
    #Great! We now have our units data, as well as a list of classes to include, and a list of
    #units to not change. Onto the randomization!
    for unit in units:
        if (unit[0].text not in unchangedUnits and unit[9].text!="Boss"):
            if not balanced:
                newclass = class_list[random.randint(0, len(class_list)-1)]
            else:
                if len(class_copy)<1: #If class copy is empty, refill it
                    class_copy = [item for item in class_list]
                newclass = class_copy.pop(random.randint(0, len(class_copy)-1))
            unit[7].text = newclass
    units_file.write("absolution_data/Data/units.xml")

def findPromotedUnits(usefulThings, units_file, units):
    '''This function adds 20 to the level of all promoted units, and returns a dictionary containing the
    unit's name as the key and their level as the value.'''
    levelMap = {}
    promotedClasses = usefulThings['promotedClasses']
    unchangedUnits = usefulThings['unchangedUnits']
    filtered_units = [unit for unit in units if unit[0].text not in unchangedUnits and unit[9].text!="Boss"]
    for unit in filtered_units:
        if unit.find("class").text in promotedClasses:
            level = int(unit.find("level").text) + 20
            unit.find("level").text = str(level)
        levelMap[unit[0].text] = unit.find("level").text
    units_file.write("absolution_data/Data/units.xml")
    usefulThings['levelMap'] = levelMap
    
def adjustPromotedLevel(units_file, units):
    '''This function sets the level of units at level 21+ to be in the range of 1-20'''
    for unit in units:
        if int(unit.find("level").text)>20:
            level = int(unit.find("level").text) - 20
            unit.find("level").text = str(level)
    units_file.write("absolution_data/Data/units.xml")
    
def promoteUnit(giveBoosts:bool, usefulThings, units_file, units):
    '''This function changes level 20+ units in unpromoted classes to their promoted counterparts, and
    level 19- units in promoted classes to their unpromoted counterparts'''
    class_file = ET.parse("absolution_data/Data/class_info.xml")
    classes = class_file.getroot()
    class_list = usefulThings['unpromotedClasses']
    promoted_classes = usefulThings['promotedClasses']
    units_to_promote = [unit for unit in units if int(unit[6].text) > 20 and unit[7].text in class_list]
    units_to_demote = [unit for unit in units if int(unit[6].text) < 21 and unit[7].text in promoted_classes]
    demo_to_promo = {item.find("long name"): item.find("turns_into").text for item in classes.findall("class") if item.find('tier')=='1'}
    #Add the troubs manually since all share the id Troubador
    demo_to_promo["Sun Troubador"] = "Sun Knight"
    demo_to_promo["Moon Troubador"] = "Moon Knight"
    demo_to_promo["Void Troubador"] = "Void Knight"
    promo_to_demo = {item.find("long name").text: item.find("promotes_from").text for item in classes.findall("class") if item.find('tier')=='2'}
    for unit in units_to_promote:
        new_class = demo_to_promo.get(unit[7].text)
        if new_class:
            unit[7].text = new_class
            if giveBoosts:
                promoGains = classes.find(f"class[long_name='{new_class}']").find("promotion").text.split(',')
                bases = unit.find('bases').text.split(',')
                newBases = ','.join([str(int(base) + int(promoGains[i])) for i, base in enumerate(bases)])
                unit.find('bases').text = newBases
    for unit in units_to_demote: 
        new_class = promo_to_demo.get(unit[7].text)
        if new_class:
            unit[7].text = new_class            
    units_file.write("absolution_data/Data/units.xml")
    
def updateWeaponRanks(usefulThings, units_file, units):
    class_file = ET.parse("absolution_data/Data/class_info.xml")
    classes = class_file.getroot()
    unchangedUnits = usefulThings['unchangedUnits']
    rank_map = {30: 'S', 21: 'A', 15: 'B', 8: 'C', 0: 'D'}
    filtered_units = [unit for unit in units if unit[0].text not in unchangedUnits and unit[9].text!="Boss"]
    for unit in filtered_units:
        wrank = rank_map[next(rank for rank in rank_map if int(unit[6].text) > rank)] #Gives a value S-D. Might need fixing
        new_wranks = ""
        class_name = unit[7].text
        if "Troubador" in class_name:
            new_wranks = '0,0,0,0,0,0,0,' + wrank + ',0'
        else:
            for item in classes.findall('class'):
                if item.find('long_name').text == unit[7].text:
                    class_wranks = item.find('wexp_gain').text.split(',')
            new_wranks = ','.join(wrank if rank != '0' else rank for rank in class_wranks)
        unit[2].text = new_wranks
    units_file.write("absolution_data/Data/units.xml")
    
def updateInventory(usefulThings, units_file, units, items_file, items, classToWeapon):
    '''This function replaces a unit's weapons with ones that match their current weapon ranks.'''
    badItems = {"Cutscene Staff", "Stale Breadstick", "Ballista", "so_Ballista", "Isolate", "Melancholy", "Neutralize",
                "RefreshItem", "UnawakenedSunna", "Hollow Blade", "Sunna", "Fang"}
    unchangedUnits = usefulThings['unchangedUnits']
    rank_map = {30: 'S', 21: 'A', 15: 'B', 8: 'C', 0: 'D'}
    items_by_wrank = {}
    wrankOrder = ["Sword", "Lance", "Axe", "Bow", "Sun", "Moon", "Void", "Staff", "Knife"]
    for item in items:
        if item.find("weapontype") != None and item.find("weapontype").text != "None" and item.find("LVL") != None and item.find("id").text not in badItems and item.find("class_locked") == None:
            weapontype = item.find("weapontype").text
            wrank = item.find("LVL").text
            if wrank not in items_by_wrank:
                items_by_wrank[wrank] = {}
            if weapontype not in items_by_wrank[wrank]:
                items_by_wrank[wrank][weapontype] = []
            items_by_wrank[wrank][weapontype].append(item.find("id").text)
    items_by_wrank["S"]["Staff"] = ["Fortify", "Warp", "Unity"]
    filtered_units = [unit for unit in units if unit[0].text not in unchangedUnits and unit[9].text != "Boss" and unit[5].text is not None]
    for unit in filtered_units:
        wrank = rank_map[next(rank for rank in rank_map if int(unit[6].text) > rank)]
        inventory = unit[5].text.split(",")
        newInventory = []
        wranks = unit[2].text.split(',')
        possibleReplacements = [items_by_wrank[wrank][weapon] for weapon in classToWeapon[unit.find('class').text]]
        if "Troubador" in unit.find('class').text or "Cleric" in unit.find('class').text:
            possibleReplacements = items_by_wrank[wrank]["Staff"] #Make sure staff classes don't start with tomes
        possibleReplacements = list(chain.from_iterable(possibleReplacements))
        if not possibleReplacements:
            possibleReplacements = ["Thunder Bangle", "Elixir", "Angelic Robe"]
        for slot in inventory:
            #item = next((item for item in items if item.find("id").text == slot), None)
            if item.find("weapontype") == None:
                newInventory.append(slot)
            else:
                newInventory.append(random.choice(possibleReplacements))
        unit[5].text = ",".join(newInventory)
    units_file.write("absolution_data/Data/units.xml")
                
def updateArts(usefulThings, units_file, units, classToWeapon):
    unchangedUnits = usefulThings['unchangedUnits']
    allArts = (usefulThings['swordArts']+usefulThings['lanceArts']+usefulThings['axeArts']+usefulThings['bowArts']
              +usefulThings['knifeArts']+usefulThings['sunArts']+usefulThings['moonArts']+usefulThings['voidArts']
              +usefulThings['tomeArts'])
    arts = {"Sword": usefulThings['swordArts'], "Lance": usefulThings['lanceArts'], "Axe": usefulThings['axeArts'],
            "Bow": usefulThings['bowArts'], "Knife": usefulThings['knifeArts'], 
            "Sun": usefulThings['sunArts'] + usefulThings['tomeArts'],
            "Moon": usefulThings['moonArts'] + usefulThings['tomeArts'], 
            "Void": usefulThings['voidArts'] + usefulThings['tomeArts']}
    filtered_units = [unit for unit in units if unit[0].text not in unchangedUnits and unit[9].text!="Boss"]
    for unit in filtered_units:
        unitClass = unit.find("class").text
        oldSkills = unit.find("skills").text.split(',')
        newSkills = [skill for skill in oldSkills if skill not in allArts and skill!= "Refresh"]
        #Now they have all their skills except a combat art
        if unitClass == "Dancer":
            newSkills.append("Refresh")
        elif unitClass in classToWeapon:
            newSkills.append(random.choice(arts[classToWeapon[unitClass][0]]))
        unit.find('skills').text = ",".join(newSkills)
    units_file.write("absolution_data/Data/units.xml")

def swapStrMagIfNeeded(usefulThings, units_file, units):
    magicClasses = usefulThings['magicClasses']
    for unit in units:
        stats = unit.find("bases").text.split(",")
        growths = unit.find("growths").text.split(",")
        unitClass = unit.find("class").text
        if ((unitClass in magicClasses) and int(growths[1]) >= int(growths[2])) or ((unitClass not in magicClasses) and int(growths[2]) > int(growths[1])):
            stats[1], stats[2] = stats[2], stats[1]
            growths[1], growths[2] = growths[2], growths[1]
            unit.find("bases").text = ','.join(stats)
            unit.find("growths").text = ','.join(growths)
    units_file.write("absolution_data/Data/units.xml")

def randomizePersonalSkills(usefulThings, units_file, units):
    status_file = ET.parse("absolution_data/Data/status.xml")
    statuses = status_file.getroot()
    newFemiTarget = ''
    newWolframTarget = ''
    unchangedUnits = usefulThings['unchangedUnits']
    staffPersonals = usefulThings['staffPersonals']
    magicClasses = usefulThings['magicClasses']
    combatPersonals = usefulThings['personalSkills']
    allPersonals = staffPersonals + combatPersonals
    staffClasses = {"Sun Troubador", "Sun Knight", "Moon Troubador", "Moon Knight", "Void Troubador",
                    "Void Knight", "Cleric", "Crusader", "Troubador"}
    combatPersonals2 = [personal for personal in combatPersonals]
    dancerPersonals = ["Defiance", 'Assertive', 'Deep Calm', 'Lucky Day', 'Lone Wolf', 'Appetite', 'Bookworm',
                       'Apathy', "Dancer's Veil", 'Small Target', 'Femi_Rally', 'Retaliator', 'Taunt_Status',
                       'Renegade', 'Return On Investment']
    filtered_units = [unit for unit in units if unit[0].text not in unchangedUnits and unit[9].text!="Boss" and unit.find("skills").text != None]
    for unit in filtered_units:
        oldSkills = unit.find("skills").text.split(',')
        newSkills = [skill for skill in oldSkills if skill not in allPersonals]
        unitClass = unit.find("class").text
        #Now we have all skills except for personals
        if unitClass in staffClasses:
            newSkills.append(staffPersonals[(random.randint(0, len(staffPersonals)-1))])
        elif unitClass == "Dancer":
            newSkills.append(dancerPersonals[(random.randint(0, len(dancerPersonals)-1))])
        else:
            if len(combatPersonals2)<1:
                newSkills.append(combatPersonals.pop(random.randint(0, len(combatPersonals)-1)))
                if "Tough Girl" in newSkills and unitClass in magicClasses:
                    newSkills[-1] = (combatPersonals.pop(random.randint(0, len(combatPersonals)-1)))
                    combatPersonals.append("Tough Girl")
            else:
                newSkills.append(combatPersonals2.pop(random.randint(0, len(combatPersonals2)-1)))
                if "Tough Girl" in newSkills and unitClass in magicClasses:
                    newSkills[-1] = (combatPersonals.pop(random.randint(0, len(combatPersonals)-1)))
                    combatPersonals2.append("Tough Girl")
            if newSkills[-1] == "Femi_Rally":
                newFemiTarget = unit.find('id').text
            elif newSkills[-1] == "Renegade":
                newWolframTarget = unit.find('id').text
        unit.find('skills').text = ",".join(newSkills)
    units_file.write("absolution_data/Data/units.xml")
    #We now have randomized personal skills. Next, we need Rally and Renegade to look at the right units when active.
    #And remove magic weapon lock on ROI so mages can use it
    for status in statuses:
        if status.find('id').text == "Return On Investment":
            #Remove magic weapon lock so mages can get it
            status.find("components").text = "gold_on_level,class_skill,untransferable"
        if status.find('id').text == "Renegade_Child":
            status.find('desc').text = status.find('desc').text.replace("Wolfram", newWolframTarget)
            status.find('pdmg').text = status.find('pdmg').text.replace("Wolfram", newWolframTarget)
            status.find('mdmg').text = status.find('mdmg').text.replace("Wolfram", newWolframTarget)
            status.find('attackspeed').text = status.find('attackspeed').text.replace("Wolfram", newWolframTarget)
            status.find('prt').text = status.find('prt').text.replace("Wolfram", newWolframTarget)
            status.find('rsl').text = status.find('rsl').text.replace("Wolfram", newWolframTarget)
            status.find('hit').text = status.find('hit').text.replace("Wolfram", newWolframTarget)
            status.find('avoid').text = status.find('avoid').text.replace("Wolfram", newWolframTarget)
            status.find('crit_hit').text = status.find('crit_hit').text.replace("Wolfram", newWolframTarget)
            status.find('crit_avoid').text = status.find('crit_avoid').text.replace("Wolfram", newWolframTarget)
        elif status.find('id').text == "Femi_Rally_Child":
            status.find('desc').text = status.find('desc').text.replace("Femi", newFemiTarget)
            status.find('pdmg').text = status.find('pdmg').text.replace("Femi", newFemiTarget)
            status.find('mdmg').text = status.find('mdmg').text.replace("Femi", newFemiTarget)
            status.find('attackspeed').text = status.find('attackspeed').text.replace("Femi", newFemiTarget)
            status.find('prt').text = status.find('prt').text.replace("Femi", newFemiTarget)
            status.find('rsl').text = status.find('rsl').text.replace("Femi", newFemiTarget)
            status.find('hit').text = status.find('hit').text.replace("Femi", newFemiTarget)
            status.find('avoid').text = status.find('avoid').text.replace("Femi", newFemiTarget)
            status.find('crit_hit').text = status.find('crit_hit').text.replace("Femi", newFemiTarget)
            status.find('crit_avoid').text = status.find('crit_avoid').text.replace("Femi", newFemiTarget)
    status_file.write("absolution_data/Data/status.xml")
    
def addBasicsToMarket():
    ch5prebase = open("absolution_data/Data/Level5/prebaseScript.txt", "a")
    ch5prebase.write("\nadd_to_market;Moonfire\nadd_to_market;Vacuum")
    ch5prebase.close()

def makePromotionsUniversal(items_file, items):
    for item in items:
        if item.find("promotion") != None:
            item.find('promotion').text = "All"
    items_file.write("absolution_data/Data/items.xml")
    
def randomizeFavoriteWeapons(usefulThings, units_file, units, items_file, items, classToWeapon):
    charNotes = open("absolution_data/Data/character_notes.txt", "r+")
    characters = charNotes.readlines()
    newCharNotes = ''
    badItems = {"Cutscene Staff", "Stale Breadstick", "Ballista", "so_Ballista", "Isolate", "Melancholy", "Neutralize",
                "RefreshItem", "Njord", "Hollow Blade", "Fang"}
    unchangedUnits = usefulThings['unchangedUnits']
    unchangedUnits += ["ValentinaY", "Raul", "Jeremy", "Cesar"]
    weaponDict = {'Sword': [], 'Lance': [], "Axe": [], "Bow": [], "Knife":[], "Sun":[], "Moon":[], "Void":[]}
    #Get a list of all items of each type
    filtered_items = [item for item in items if ((item[0].text not in badItems)
                      and (item.find("class_locked") == None) and (item.find("weapontype") != None))]
    for item in filtered_items:
        weapon_type = item.find("weapontype").text
        if weapon_type in weaponDict:
            weaponDict[weapon_type].append(item[0].text)
    filtered_units = [unit for unit in units if unit[0].text not in unchangedUnits and unit[9].text!="Boss"
                      and unit.find('class').text!="Dancer"]
    for unit in filtered_units:
        unitClass = unit.find("class").text
        if "Staff" in classToWeapon[unitClass][-1]: #Can't have staves as favorites
            newFavorites = random.sample((weaponDict[classToWeapon[unitClass][0]]), 5)
        else:
            newFavorites = random.sample((weaponDict[classToWeapon[unitClass][0]]+weaponDict[classToWeapon[unitClass][-1]]), 5) if unitClass != "Dancer" else []
        favorites = 'Favorite Items|' + ','.join(newFavorites)
        for character in characters:
            #Find the line in character_notes that has our current unit
            if unit[0].text in character[:13]:
                info = character.split(';')
                info[4] = favorites
                newCharacter = ';'.join(info)
                newCharNotes += newCharacter + '\n' #Think this'll fix Val not having favorites
    charNotes.close()
    charNotes = open("absolution_data/Data/character_notes.txt", "w+")
    charNotes.write(newCharNotes)

def removeWeaponLock(items_file, items):
    for item in items:
        if item.find('LVL') != None:
            lvl = item.find("LVL").text
            if lvl == "Valentina":
                item.find("LVL").text = "D"
            elif lvl in {"Sanite", "Thelma", "Reese"}:
                item.find("LVL").text = "C"
    items_file.write("absolution_data/Data/items.xml")

#This implementation might shuffle the original levelmap, but I don't think so
def mapCharToReplacement(usefulThings):
    player_characters = list(usefulThings['levelMap'].keys())
    player_characters.remove("Valentina")
    random.shuffle(player_characters)
    newOrder = {key: player_characters.pop() for key in usefulThings['levelMap'] if key != "Valentina"}
    newOrder["Valentina"] = "Valentina"
    return newOrder

def scaleLevels(usefulThings, newOrder, units_file, units):
    #This first part remaps levels to the unit they replace
    for unit in units:
        if unit[0].text in usefulThings['levelMap']:
            stats = unit.find("bases").text.split(",")
            growths = unit.find("growths").text.split(",")
            oldLevel = int(unit.find('level').text)
            newLevel = int(usefulThings['levelMap'][newOrder[unit[0].text]])
            levelDiff = newLevel - oldLevel
            i = 0
            for growth in growths: #this scales their stats to match their new level
                stats[i] = round(float(stats[i]) + (int(growth)/100)*levelDiff)
                i+=1
            unit.find('level').text = str(newLevel)
            unit.find("bases").text = ",".join(str(s) for s in stats)
    units_file.write("absolution_data/Data/units.xml")
    
def updateRecruitmentOrder(usefulThings, newOrder):
    flippedNewOrder = {v: k for k, v in newOrder.items()}#This way it reads unit:replaced by instead of replacement:original
    print(flippedNewOrder)
    filesToChange = {'/interactScript.txt':"", '/introScript.txt':"", '/outroScript.txt':"", '/prebaseScript.txt':"",
                     '/fightScript.txt':"", '/turnChangeScript.txt':"", '/unitLevel.txt':"", '/talkScript.txt':"",
                     '/villageScript.txt':"", '/narrationScript.txt':"", '/baseScript.txt':"", '/waitScript.txt':""}
    for i in range(1, 23):
        charInChapter = {'Ramon':False, 'Salvador':False, 'Lakshmi':False, 'Eduardo':False, 'Evelia':False, 'Trudy':False,
                         'Cecile':False, 'Gabriel':False, 'Bennett':False, 'Quentin':False, 'Jean': False, 'Zahir':False,
                         'Agnes':False, 'Dayo':False, 'Idowu':False, 'Reese':False, 'Ojala':False, 'Sanite': False,'Hati': False,
                         'Yewande':False, 'Nadia':False, 'Femi':False, 'Persephone':False, 'Mitzi':False, 'Rhapsody':False,
                         'Mackenzie':False, 'Velma':False, 'Thelma':False, 'Xavier':False, 'Hildegard':False, 'Balthazar':False,
                         'Tybalt': False, 'Wolfram':False, 'Fabrice':False, 'Tchaka':False}
        filepath = f"absolution_data/Data/Level{i}"
        for file in filesToChange:
            if os.path.exists(filepath+file):
                workingFile = open(filepath+file, "r")
                filesToChange[file] = workingFile.read()
                for key in flippedNewOrder:
                    if key in filesToChange[file]:
                        charInChapter[key] = True
                workingFile.close()
        #Now we've read all the files, and found the characters who need to be replaced this chapter
        for file in filesToChange: #Loop back through, this time to edit
            if os.path.exists(filepath+file):
                workingFile = open(filepath+file, "w")
                filesToChange[file] = filesToChange[file].replace("TchakaC","Tchaka") #Account for convoy Tchacka
                for key in flippedNewOrder:
                    if charInChapter[key]:#Replace original instance of chars with chars1 so we don't replace replacements
                        filesToChange[file] = filesToChange[file].replace(key,key+'1')
                    if i == 4: #Account for AllySanite
                        filesToChange[file] = filesToChange[file].replace("AllySanite1", "AllySanite")
                        filesToChange[file] = filesToChange[file].replace("Bennett1Custom","BennettCustom")#AI fix
                    elif i == 9: #Account for boss Hildegard
                        filesToChange[file] = filesToChange[file].replace("BHildegard1", "BHildegard")
                    elif i == 12:
                        filesToChange[file] = filesToChange[file].replace("Mackenzie1Custom_MudArmors1","MackenzieCustom_MudArmors1") #AI fix
                for key in flippedNewOrder:
                    if charInChapter[key]: 
                        #Replace the originals, identified by the 1
                        filesToChange[file] = filesToChange[file].replace(key+'1',flippedNewOrder[key])
                        filesToChange[file] = filesToChange[file].replace(key+"Custom","TybaltCustom") #AI fixes
                        filesToChange[file] = filesToChange[file].replace("Follow"+key,"FollowHildegard") #AI fixes
                workingFile.write(filesToChange[file])
                workingFile.close()
                filesToChange[file] = filesToChange[file].replace("HBildegard","BHildegard")#Change back after modifying other units
                filesToChange[file] = filesToChange[file].replace("SallyAnite","AllySanite")
        i+=1
    workingFile = open('absolution_data/Data/death_quote_info.txt', "r")
    deathQuotes = workingFile.read()
    workingFile.close()
    workingFile = open('absolution_data/Data/death_quote_info.txt', "w")
    for key in flippedNewOrder:
        deathQuotes = deathQuotes.replace(key,key+'1')
    for key in flippedNewOrder:
        deathQuotes = deathQuotes.replace(key+'1',flippedNewOrder[key])
    workingFile.write(deathQuotes)
    workingFile.close()

def main(usefulThings, units_file, units, items_file, items, classToWeapon):
    randClasses = False
    findPromotedUnits(usefulThings, units_file, units)
    print('Welcome to the Absolution randomizer! Be warned that it is currently incomplete, and is probably a buggy mess.')
    print("As of now, it can randomize player classes (Promotion items are made universal). Type 'Y' if you want to randomize classes, 'N' if not." )
    randClassesInput = input()
    if randClassesInput == "Y" or randClassesInput == 'y':
        randClasses=True
    if randClasses:
        print("Would you like to randomize Valentina's class? Y or N")
        randLord = input()
        if randLord == "Y" or randLord == 'y':
            randLord=True
        else:
            randLord=False
        print("Would you like to randomize thieves? Doing so may make some treasure unobtainable. Y or N")
        randThieves = input()
        if randThieves == "Y" or randThieves == 'y':
            randThieves=True
        else:
            randThieves=False
        print("Would you like to randomize dancers? Y or N")
        randDancer = input()
        if randDancer == "Y" or randDancer == 'y':
            randDancer=True
        else:
            randDancer=False
        print("Would you like to have balanced class distribution? Y or N")
        classBalance = input()
        if classBalance == "Y" or classBalance == 'y':
            classBalance=True
        else:
            classBalance=False
        removeWeaponLock(items_file, items)
        makePromotionsUniversal(items_file, items)
        randomize_classes(randLord, randThieves, randDancer, False, classBalance, usefulThings, units_file, units)
        promoteUnit(False, usefulThings, units_file, units)
        updateWeaponRanks(usefulThings, units_file, units)
        updateInventory(usefulThings, units_file, units, items_file, items, classToWeapon)
        updateArts(usefulThings, units_file, units, classToWeapon)
        swapStrMagIfNeeded(usefulThings, units_file, units)
        addBasicsToMarket()
        randomizeFavoriteWeapons(usefulThings, units_file, units, items_file, items, classToWeapon)
    else:
        print("Would you like to randomize combat arts? Y or N")
        randArts = input()
        if randArts == "Y" or randArts == 'y':
            updateArts(usefulThings, units_file, units, classToWeapon)
        print("Would you like to randomize favorite weapons? Y or N")
        randFavorites = input()
        if randFavorites == 'y' or randFavorites == "Y":
            randomizeFavoriteWeapons(usefulThings, units_file, units, items_file, items, classToWeapon)
    print("Would you like to randomize personal skills? Y or N")
    randSkills = input()
    if randSkills == "Y" or randSkills == 'y':
        randomizePersonalSkills(usefulThings, units_file, units)
    print("Would you like to randomize recruitment order? Valentina and the prologue crew will be unaffected. Y or N")
    randRecruitment = input()
    if randRecruitment == 'y' or "Y":
        newOrder = mapCharToReplacement(usefulThings) #This will create a map where the old char is key and new is value
        scaleLevels(usefulThings, newOrder, units_file, units) #This will scale a unit's level and bases to match what they should be in their new slot
        promoteUnit(True, usefulThings, units_file, units) #This will adjust promoted/unpromoted class to match level and apply promo gains
        updateRecruitmentOrder(usefulThings, newOrder) #BIG ONE: This will update the various .txt files for recruitment. Will almost certainly need helpers and a lot of work.
        updateWeaponRanks(usefulThings, units_file, units)
        updateInventory(usefulThings, units_file, units, items_file, items, classToWeapon)
    adjustPromotedLevel(units_file, units)
    
units_file = ET.parse("absolution_data/Data/units.xml")
units = units_file.getroot()
items_file = ET.parse("absolution_data/Data/items.xml")
items = items_file.getroot()

usefulThings = {"unpromotedClasses": {'Myrmidon','Mercenary','Soldier','Hoplite','Pirate','Fighter',
                    'Archer','Gunner','Sun Mage','Moon Mage','Void Mage','Cleric',
                    'Sword Cavalier','Lance Cavalier','Bow Cavalier','Axe Cavalier',
                    'Sun Troubador','Moon Troubador','Void Troubador',
                    'Sword Armor','Lance Armor','Axe Armor',
                    'Eagle Knight','Pegasus Knight','Dracoknight','Sunwing','Moonwing','Darkwing',
                    'Thief','Spy','Adelita','Dancer'},
                "promotedClasses": {'Swordmaster','Hero','Halberdier','Phalanx','Berserker','Warrior',
                    'Sniper','Arbalest','Sun Sage','Moon Sage','Void Sage','Crusader',
                    'Sword Paladin','Lance Paladin','Bow Paladin','Axe Paladin',
                    'Sun Knight','Moon Knight','Void Knight',
                    'Sword General','Lance General','Axe General',
                    'Griffon Knight','Falcoknight','Dracolord','Seraph','Leviathan','Harrier',
                    'Assassin','Rogue','Coronela'},
                "unchangedUnits": ['Strega','Horatio','Iris','Delilah','Skoll','Enceladus','AllySanite', 'Carmichael',
                    'Wolfram14x','Wagon1','Wagon2','Wagon3','Wagon4','Wagon5', 'Zess', 'Disguisedt', 'Disguisedv',
                    'Carmen', 'Toussainte', 'Luciano', 'Esteban', 'Jacinta', 'Diego', 'ValentinaY', 'Jeremy', 'Cesar',
                    'Raul', 'Rafael', 'Lorraine', 'Kayin', 'Ugne', 'Isaiah', 'Jericho', "SkollB", "NPCJericho"],
                "swordArts":["Solar Flare", "Foudroyant", "Blade Crash", "Grounder", "Haze Slice", "Soulblade", "Seiryu Strike", "Defiant Edge"],
                "lanceArts":["Windsweep", "Tempest Lance", "Double Time", "Knightkneeler", "Frozen Lance", "Moon Phase"],
                "axeArts":["Diamond Cutter", "Wild Abandon", "Helm Splitter", "Crimson Axe", "Raging Storm", "Shaker Edge"],
                "bowArts":["Pierce", "Crossblast", "Hunters Volley", "Enclosure"],
                "knifeArts":["Critical Strike", "Finesse Blade", "Bedlam Burst", "Backstep"],
                "tomeArts": ["Insight", "Refresh_Art", "Apotrope"],
                "sunArts": ["Prism"],
                "moonArts": ["Tigerstance"],
                "voidArts": [],
                "magicClasses": {"Sun Mage", "Sun Sage", "Moon Mage", "Moon Sage", "Void Mage", "Void Sage",
                    "Sunwing", "Seraph", "Moonwing", "Leviathan", "Darkwing", "Harrier", "Cleric", "Crusader",
                    "Sun Troubador", "Moon Troubador", "Void Troubador"},
                "personalSkills": ["Defiance", "Assertive", "Deep Calm", "Fleeting Confidence", "Elbow Grease",
                    "Easy Way Out", "Lucky Day", "Meet n Greet", "Duelist", "Dive Bomb", "Moxie", "Experimenter",
                    "Scout", "New Threads", "Lone Wolf", "Appetite", "Vitality", "Lost Disciple",
                    "Technician", "Bookworm", "Solar Power", "Apathy", "Tough Girl", "Dancer's Veil", "Small Target",
                    "Femi_Rally", "Impatience", "Protector", "Domination", "Grudge", "Retaliator", "Taunt",
                    "Soul Heart", "Renegade", "Return On Investment"],
                "staffPersonals": ["Fire Balm", "Earth Balm", "Wind Balm", "Thunder Balm", "Spectrum Balm"],
}

classToWeapon = {"Adelita": ["Sword"], "Coronela": ["Sword", "Bow"], "Mercenary": ["Sword"], "Hero": ["Sword", "Axe"], "Myrmidon": ["Sword"],
                "Swordmaster": ["Sword"], "Sword Armor": ["Sword"], "Sword General": ["Sword", "Lance"], "Eagle Knight": ["Sword"],
                "Griffon Knight": ["Sword", "Bow"], "Sword Cavalier": ["Sword"], "Sword Paladin": ["Sword"], "Hoplite": ["Lance"],
                "Phalanx": ["Lance", "Sword"], "Soldier": ["Lance"], "Halberdier": ["Lance"], "Lance Armor": ["Lance"],
                "Lance General": ["Lance", "Axe"], "Pegasus Knight": ["Lance"], "Falcoknight": ["Lance", "Sword"], "Lance Cavalier": ["Lance"],
                "Lance Paladin": ["Lance"], "Fighter": ["Axe"], "Warrior": ["Axe", "Bow"], "Pirate": ["Axe"], "Berserker": ["Axe"],
                "Axe Armor": ["Axe"], "Axe General": ["Axe", "Sword"], "Dracoknight": ["Axe"], "Dracolord": ["Axe", "Lance"], 
                "Axe Cavalier": ["Axe"], "Axe Paladin": ["Axe"], "Cleric": ["Axe", "Staff"], "Crusader": ["Axe", "Staff"], "Gunner": ["Bow"],
                "Arbalest": ["Bow", "Lance"], "Archer": ["Bow"], "Sniper": ["Bow"], "Bow Cavalier": ["Bow"], "Bow Paladin": ["Bow"], 
                "Thief": ["Knife"], "Rogue": ["Knife"], "Spy": ["Knife"], "Assassin": ["Knife"], "Sun Mage": ["Sun"], "Sun Sage": ["Sun"], 
                "Sunwing": ["Sun"], "Seraph": ["Sun", "Sword", "Staff"], "Sun Troubador": ["Sun", "Staff"], "Sun Knight": ["Sun", "Staff"], 
                "Moon Mage": ["Moon"], "Moon Sage": ["Moon"], "Moonwing": ["Moon"], "Leviathan": ["Moon", "Axe"], "Dancer": [],
                "Moon Troubador": ["Moon", "Staff"], "Moon Knight": ["Moon", "Staff"], "Void Mage": ["Void"], "Void Sage": ["Void"],
                "Darkwing": ["Void"], "Harrier": ["Void", "Lances"], "Void Troubador": ["Void"], "Void Knight": ["Void", "Staff"]}
main(usefulThings, units_file, units, items_file, items, classToWeapon)
