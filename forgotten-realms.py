# pip3 install anthropic
# CLAUDE_API_KEY env var also required. https://console.anthropic.com/
# usage: forgotten-realms.py [-h] [--model MODEL] [--api API] [--language LANGUAGE]

# Process files in specified folders.

# options:
#   -h, --help           show this help message and exit
#   --model MODEL        Anthropic model to use: "sonnet", "opus", or "haiku" (default: "sonnet")
#   --api API            API to use: "anthropic" or "google" (default: "anthropic")
#   --language LANGUAGE  Language for the narrator: for example "українська", or "Ukrainian"

import anthropic
import argparse
import json
import os
import sys
from termcolor import colored
import threading
import time



def clear_input():
    # Clear the input buffer
    try:
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    except ImportError:
        import termios
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)


class RPGGame:
    def __init__(self, client, model, language="English"):
        self.client = client
        self.model = model
        self.context = "Chatacter posesses 58 coins and usual folk robes. His skills are yet to be discovered."
        self.history_message_num = 0
        self.language = language
        # self.total_usage = 0


    def narrator(self, system_message, user_input):
        narration = ""
        self.history_message_num += 1
        # print(colored("+       +","yellow"), end="", flush=True)
        with self.client.messages.stream(
            model=self.model,
            max_tokens=600,
            temperature=0.7,
            system=system_message + " Context: " + self.context,
            messages=[
                    {"role": "user", "content": user_input + " This is interaction number " + str(self.history_message_num) + " with player."}
                ,   {"role": "assistant", "content": """Narrator:
<Narration>"""}
                ]
        ) as stream:
            for text in stream.text_stream:
                narration += text
                print(colored(text,"yellow"), end="", flush=True)
            # self.total_usage += stream.usage["prompt_tokens"] + stream.usage["completion_tokens"]
        print()
        print()
        return narration

    def context_maker(self, system_message, narration, user_input):
        with self.client.messages.stream(
            model=self.model,
            max_tokens=1500,
            temperature=0.2,
            system=system_message,  # Pass the system message as a top-level parameter
            messages=[
                    {"role": "user", "content": f"""<Previous context>ITEMS: {self.context}</Previous context>
<Narration>{narration}</Narration>

<Player input>{user_input}</Player input>"""}
                ,   {"role": "assistant", "content": "<New context>MAP JSON:"}
            ]
        ) as stream:
            context = ""
            for text in stream.text_stream:
                context += text
                print(colored(text,"black", "on_cyan"), end="", flush=True)
        print()
        print()

            # self.total_usage += stream.usage["prompt_tokens"] + stream.usage["completion_tokens"]
            # self.context = context[:1500]  # Truncate context to 1500 tokens
        self.context = context

    def play(self):
        narrator_system_message = f"""You are an AI Dungeon Master / narrator for an RPG game set in Forgotten Realms.
Describe the game world, suggest some possible actions (user should know he can write his own alternative), and request input for player's next action.
Try to write your output with less than 130 words. Provide clues to help us map out our surroundings.
We never simulate <Player Input/> - that's up only for the player to decide.
We always paint characters we talk to in carefully crafted 15x10 ASCII art, if we're talking to somebody. 
Max out use of emojis to support words.
<Example narration>
You enter the Tavern 🍻, hoping to find someone generous to talk to.

Tavern Keeper:
     ___
    /   \
   | o_o |
    \\ _ /
  /\\_____/\
 |_________|

"Welcome traveler! 🤗 What brings you to my tavern? Drink 🍺 and 🗣 talk?"
</Example narration>
Only output narration, nothing more. End output when narration ends, right before </Narration> tag.
When my speech is presented, please, also present an answer from someone I talk to, or Universe. Try to be dense in action.
Narration ends on a note that requires further player input.
Speak {self.language} language."""

        context_maker_system_message = """You are an AI context rememberer for an RPG game. Keep track in ENGLISH language.
Update and maintain the game context based on the narrator's output and the player's input, keeping the output context within 900 words.
Consider to store short and long term memory, what is needed and what to discard. You must keep in memory all of the important facts about setting and character, for us to be able to fully deconstruct current situation, location and the world, intents, etc. and all important historical events. Be short and concise, but keep track of anything of importance, even if it's not relevant at the moment. Clearly remember the player's previous request and what we're up to right now. You don't do \"Narration:\", you only output context! When buying or anyone is set to be performing any actions, you have to consider if we can afford it and if we are able to perform actions successfully, or if an action is to be denied.
STRUCTURE and REMEMBER CONTEXT, update location, posessions, relationship info, keep track of previous actions by all characters and possible options, discard now-unimportant details, etc. You can make an <ANALYSIS/>, but not narrate new things.
Don't narrate. Don't provide next step information. Only provide context up to the point of player's action and it's validity.
Monospaced font is used. Count all of the characters carefully.
DON'T ADVANCE CONVERSATIONS AND PRODUCE CONSEQUENCES! Anything said will not be seen by the player.
Something more or less important happens on every step, this world never goes stale. 
Map out and update a JSON of places inside the world and their hierarchies, what's inside what, as well as a short description of notable features. 
We also put items of characters and their properties inside character's props of world map JSON.
Maintain and keep up to date assumed positions of characters and their properties inside the map. Keep clear track of time and remember hour, minute, day of week, day of month, etc."""
        
        # print("Welcome to the AI-powered RPG game!")
        print(colored("Welcome to the AI-powered RPG game!", "cyan"))
        user_input = "Lets explore the Realm!"
        while True:
            # narration = self.narrator(narrator_system_message, "")
            # print(colored(f"\nNarrator: {narration}", yellow))
            
            narration = self.narrator(narrator_system_message, user_input)
            # print(f"\nNarrator: {narration}")
            sys.stdin.flush()

            timer = threading.Timer(0.5, clear_input)
            timer.start()

            # Wait for user input
            # user_input = sys.stdin.readline().strip()

            # Cancel the timer if the user responds within 0.5 seconds
            time.sleep(1)
            timer.cancel()

            while True:
                user_input = input(colored("\n\nMe: ", "black", "on_green") + " ")
                if user_input.strip():
                    break
                print("Please say something..")
                print()
            print()
            print()
            self.context_maker(context_maker_system_message, narration, user_input)
            # print(colored(f"\nTotal tokens used: {self.total_usage}", "red"))
            
            # choice = input(colored("Continue playing? (y/n): ", "magenta"))
            # if choice.lower() != 'y':
            #     break
        print("Thanks for playing!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process files in specified folders.')
    parser.add_argument('--model', type=str, help='Anthropic model to use: "sonnet", "opus", or "haiku" (default: "sonnet")', default='sonnet')
    parser.add_argument('--api', type=str, help='API to use: "anthropic" or "google" (default: "anthropic")', default='anthropic')
    parser.add_argument('--language', type=str, help='Language for the narrator: for example "українська", or "Ukrainian"', default='English')
    args = parser.parse_args()
    api_key = os.environ.get('CLAUDE_API_KEY')
    if not api_key:
        raise ValueError('CLAUDE_API_KEY environment variable is not set.')

    if args.api == 'anthropic':
        client = anthropic.Anthropic(api_key=api_key)
        if args.model == 'sonnet':
            model = "claude-3-sonnet-20240229"
        elif args.model == 'opus':
            model = "claude-3-opus-20240229"
        elif args.model == 'haiku':
            model = "claude-3-haiku-20240307"
        else:
            raise ValueError(f"Invalid model: {args.model}. Choose 'sonnet', 'opus', or 'haiku'.")
    else:
        raise ValueError(f"Invalid API: {args.api}. Only 'anthropic' is supported.")

    game = RPGGame(client, model, args.language)
    game.play()
