using PawnsOfDivinity.Core.Characters;

namespace PawnsOfDivinity.Core.Characters.Definitions;

public static class Assassin
{
    public static CharacterDefinition Definition => new(
        Id: "assassin",
        Name: "Assassin",

        Description: "A deadly assassin who relies on speed, precision, and lethal strikes to eliminate enemies.",

        BaseStats: new CharacterStats(
            MaxHealth: 30,
            Strength: 16,
            Defense: 5,
            Resistance: 6,
            Dexterity: 18,
            Speed: 17,
            Constitution: 6,
            Intelligence: 8,
            Wisdom: 5,
            Charisma: 9
        )
    );
}