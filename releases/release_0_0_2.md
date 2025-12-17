## Release 0.0.2

### Implemented

* Character creation UI
* Start game with character with selected parameters
* It's possible to play the game by using default character


### Details

Role-play system based on Mass Effect D20 rules. 

Available races: Asari, Batarian, Drell, Elcor, Human, Krogan, Quarian, Salarian, Turian, Volus and Vorcha. All of them are described in the table ```races.2da```. Each race has bonus/penality to the abilities. This bonus describe in the table ```abracead.2da```. The table ```abrcerq.2da``` contains minimal and maximum ability values when create the character. The table ```racethac.2da``` contains additional BAB (Base Attack Bonus) for weapon proficiency for each race. In our case all the additional bonus is 0.

Available classes: Adept, Engineer, Infiltrator, Sentinel, Soldier, Vanguard, Asari Pure Biotic, Asari Huntress, Asari Scientist, Batarin Brawler, Drell Assassin, Elcor Living Tank, Human Explorer, Krogan Battlemaster, Quarian Mechanist, Slarian Scientist, Turain Agent, Volus Protector, Vorch Hunter. These classes described in the table ```classes.2da```. Available classes depends on the selected race. What class is available for each race defined in this table. The table ```clskills.2da``` contains only one essential column ```NO_PROF``` which contains value ```-4``` for the BAB penality if the character attack by the weapon without proficiency. For each class level xp defined in the table ```xplevel.2da```. The table ```thac0.2da``` contains BAB value for each level. The table ```clssaves.2da``` contain values for Fortitude, Reflex and Will saves.

Each character has standard abilities: Strength, Dexterity, Constitution, Intelligence, Wisdom and Charisma. They are described in the table ```abchar.2da```. There are 10 ability points, available when the character is created. For now only Dex, Con and Int are used in the system. Dex define the BAB, it increase the BAB from ```thac0.2da``` by the ```[Dex]``` - Dex modifier. Also Dex define the character Defence by the formula ```Def = 10 + [Dex]```. Con define the number of hit points. It calculated as ```4 x(HP + [Con])```, where ```HP``` value defined in the table ```classes.2da``` (```HP``` column). Int define the number of skill points.

There are 16 available skills: Biotics, Electronics, Bluff, Concentration, Diplomacy, Decryption, Hide, Intimidate, Knowledge, Move Silently, Hacking, First Aid, Search, Medicine, Heavy Weapon, Research. Originally, in MEd20 there are many skills. But these skills used in the table game when the character appear in some game situation. In the computer rpg (based on IE) only limited scenarios of using skills are available. Another reason, why there are only 16 skills, it the engine limitations. We use IWD2 character setups, because these character have the biggest inventar, support 16 skills and support feats system. All skills are described in the table ```skills.2da```. When create the character, the number of available skill points depend on the class. It's described in the table ```classes.2da``` (column ```SP```). The number of skill points is equal to ```SP + [Int]```, where ```[Int]``` in the Intelligence modifier. If the skill is class-skill, then it require only one skill point. If the skill is not class-skill, then to upgrade one level it require 2 points. How many points required for each skill for each class described in the table ```cls2skl.2da```.

Original MEd20 contains many different feats, available for characters. We adopt only some of them. Mostly it's weapon feats. Used IWD2 character format allows to define many feats, but only 26 of them allows to have discrete levels. The table ```featreq.2da``` contains available feats: for weapons, ammo types and armor. The table ```clsfeats.2da``` contains feats, which already learned by different classes. At the creation process it's available to add any new feat. The table ```wspatck.2da``` contains the number of attack per one round, when the character ues the weapon. If the character use the weapon without correspondence feat, then it can use only one attack per round (the row ```0``` in the table). If it has non-zero level, then the number of attacks contains in other rows. Column of the table ```wspatck.2da``` corresponds to the warrior level of the character. We does not define these levels, so, always use the firs column (which corresponds to the warrior level 0).


### Screenshots

[create character](./images/ui_01.png)

[select the race](./images/ui_02.png)

[select the class](./images/ui_03.png)

[define abilities](./images/ui_04.png)

[upgrade skills](./images/ui_05.png)

[select feat](./images/ui_06.png)