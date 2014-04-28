gnome-fortress
==============

Objective
---------
Dig down to explore the world! Try to collect as many diamonds as you can and bring them bach to the surface!

Using Tools
-----------
Each of your four starting gnomes has a different tool. The pick can be used to mine, the sickle can be used to harvest, the ladder can be used to climb back up, and the hammer can be used to craft more tools. Press X to pick up a tool (or resource) and C (or C with an arrow key to specify the direction) to use it. Tools wear out over time. Each tool has 100 charges in the beginning. Mining ore or diamonds wears the pick down faster.

Crafting
--------
In order to craft, pile up the crafting ingredients in one place and use a hammer. If the available ingredients form a valid recipe, they will be transformed into a tool. If there are more raw materials around than you need, crafting will fail. These recipes are possible: 

    wood+wood+wood=ladder
    wood+wood+iron=hammer
    wood+iron+iron=pickaxe
    wood+iron=sickle

Food
----
The current food energy level of each gnome is shown at the top of the screen. If the energy level falls below 20, it can not use tools. You can increase energy by eating food (pick up with X, eat with C). A hungry gnome automatically eats any food he finds next to him until he is no longer hungry. The initial energy level should last for five minutes.

Loops
-----
You can automate complex tasks by giving a gnome looping instructions. Press R to record an instruction sequence, then give your instructions, then press again to start the sequence. Controlling a gnome again stops the loop. You can switch to other gnomes with J and K while a loop is executed.