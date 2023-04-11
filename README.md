# Absolution-Randomizer
Randomizer for the fangame Absolution by ZessDynamite

Disclaimer: I am not the developer for Absolution. I've merely built this randomizer for it because I enjoy the game.
Absolution download: https://feuniverse.us/t/lex-talionis-absolution-22-32-chapters/7045/123
(Try the game! It's fun.)

Welcome to the Absolution Randomizer! If you’re unfamiliar with what a randomizer is, it takes an existing Fire Emblem game (in this case, Absolution) and applies a series of changes to mix things up in wacky and interesting ways. As of right now, this randomizer can:
- Randomize unit’s classes
    - Options for excluding lords/thieves/dancer
    - Option for balancing class selection (roughly even number of each class) or true random class distribution
- Randomize a unit’s Favorite Weapons (done automatically with classes)
- Randomize unit’s combat arts (done automatically with classes)
- Randomize personal skills
- Randomize recruitment order (Valentina excluded)
Before you start, here’s some quick warnings:
- Play the base game first! It’s a lot of fun. 
- To say I’ve tested this lightly is an overstatement; there will be lots of bugs, crashes, and various game-breaking interactions. If that’s the case, just send your debug.log and/or a screenshot, and I’ll see what I can do. Most errors will be fixable with a small change to a game file or dev commands.
- Things will not be balanced. Some units will be incredible, others will be hot garbage.
- On that note, it is entirely possible to get softlocked, particularly in chapter 4, depending on who replaces Gabriel. 
- If you have an antivirus, it may not like the randomizer, since it does edit other files. If this happens, just tell your antivirus to ignore the program.
- Always randomize a fresh copy. Weird stuff happens when you don’t.
- This randomizer works with v0.3.22.0 of Absolution. When a new version drops, I’ll likely (but not always) have to update it. 
To get it started, just place the Absolution Randomizer file in the same folder as the double_click_to_play.bat file, and run the randomizer. Once it’s finished, boot up Absolution and have fun! (And don’t forget to share your particularly busted/awful units!)
Lastly, some known bugs/issues:
- Units who start as NPCs randomizing to certain classes crashes the game. These will become less common as the game nears completion.
- Some classes have buggy or nonexistent animations, for combat or as a map sprite. These are rarely game-crashing, and will gradually be addressed.
- Not really a bug, but the mage units are bad if randomized to most physical classes due to their low con. I’m open to suggestions for how to fix this.
- Reese will join with an empty inventory in random recruitment, and always have a killing edge regardless of class if doing standard recruitment. This is because her inventory is created with events.
- Xavier’s replacement will automatically join your side after your first unit moves when doing random recruitment. 
- Random recruitment is the least-tested feature, and may result in issues like having two of a unit, having a unit not appear or be unrecruitable, etc. As you find these errors, let me know! I think I’ve caught them all, but you never know.
