import pyttsx3


with open("voice.txt", "r") as voice_data:
    my_voice_data = voice_data.readlines()


class VoiceManager:
    def __init__(self):
        self.my_language = int(my_voice_data[0])
        self.speed_rate = int(my_voice_data[1])

        self.engine = pyttsx3.init()
        # Speed rate
        self.engine.setProperty("rate", self.speed_rate)
        # Language
        self.voices = self.engine.getProperty("voices")
        self.voice = self.voices[self.my_language]

    def chooseSpeedRate(self):
        try:
            self.speed_rate = int(input("\nSelect the voice speed rated\n"
                                        "Recommended a number between 140(slower) and 160(faster): "))
        except ValueError:
            print("\nYou must choose a number!\n")
            self.chooseSpeedRate()

    def changeSpeedRate(self):
        print(f"\nActual speed rate: {self.speed_rate}\n")
        change_speedR = input("Do you want to change the voice speed rate\n"
                              "Select y/n: ").lower()
        answers = ("y", "n")
        while not change_speedR in answers:
            print("\nWrong answer!\n")
            change_speedR = input("Do you want to change the voice speed rate\n"
                                  "Select y/n: ").lower()
        if change_speedR == "y":
            self.chooseSpeedRate()
            self.engine.setProperty("rate", self.speed_rate)
            with open("voice.txt", "w") as my_new_voice_data:
                my_new_voice_data.write(f"{self.my_language}\n{self.speed_rate}")
            print(f"Voice speed rate was changed to {self.speed_rate}!")

    def selectReaderLanguage(self):
        i = 1
        options = []
        actual_language = self.voice.name.split('-')[1].split()[0]

        print(f"\nActual language: {actual_language}\n")
        change_language = input("Do you want to change language\n"
                                "Select y/n: ").lower()
        answers = ("y", "n")
        while not change_language in answers:
            print("\nWrong answer!\n")
            change_language = input("Do you want to change language\n"
                                    "Select y/n: ").lower()
        if change_language == "y":
            for voice in self.voices:
                language = voice.name.split('-')[1].split()[0]

                print(f"Available voices {i}: {language}")
                options.append(str(i))
                i += 1

            choose = input("\nChoose voice by its number: ")
            while not choose in options:
                print("You must choose one of the enumerated options")
                choose = input("\nChoose voice by its number: ")
            choose = int(choose) - 1
            self.voice = self.voices[choose]
            choose = str(choose)
            with open("voice.txt", "w") as my_new_voice_data:
                my_new_voice_data.write(f"{choose}\n{self.speed_rate}")
                actual_language = self.voice.name.split('-')[1].split()[0]
                print(f"\nLanguage was changed to {actual_language}!")


class Voice:
    @staticmethod
    def read(voice, file_extension, folder_dir, files_data):
        count = 0
        zeros = "000"

        for data_name in files_data:

            print(f"\nThere are {len(files_data) - count} items to read!\n")

            file_name = data_name + ".mp3"
            print(f"Reading {data_name}...")

            if file_extension == "TXT":
                voice.engine.setProperty("voice", voice.voice.id)
                voice.engine.save_to_file(files_data[data_name], f"{folder_dir}{file_name}")
                voice.engine.runAndWait()
                print(f"Done! The file was created in {folder_dir}! :)")

                count += 1
            else:

                if count > 100:
                    zeros = "0"
                elif count < 10:
                    zeros = "000"
                elif count > 9:
                    zeros = "00"

                voice.engine.setProperty("voice", voice.voice.id)
                voice.engine.save_to_file(files_data[data_name], f"{folder_dir}{zeros}{count} - {file_name}")
                voice.engine.runAndWait()
                print(f"Done! The file was created in {folder_dir}! :)")

                count += 1
