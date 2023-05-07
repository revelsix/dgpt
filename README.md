# dgpt
a fork of dggpt designed for use as a discord chat bot

this fork also tracks how many times a user has used the bot and allows you to limit them to a certain number of uses per day. neat.

``cp sample-config config``

``cp sample-system.txt system.txt``

## current limitations
- discord emotes suck so much i hate them (for example, OMEGALUL would be <:OMEGALUL:629446114906472455>). probably possible for gpt to type that consistently if i bothered changing base.json but that's a problem for future me to solve
- haven't added support for slash commands yet (**DO NOT LOOK AT `main.py`** Aware)
- dgg specific features like emotes and phrases were gutted from this version 