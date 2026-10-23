using PawnsOfDivinity.Core.Characters;

namespace PawnsOfDivinity.Core.Characters.Definitions;

public static class Healer
{
    public static CharacterDefinition Definition => new(
        Id: "healer",

        Name: "Healer",

        Description: "A devoted healer who restores allies and protects them from danger.",

        BaseStats: new CharacterStats(
            MaxHealth: 34,
            Strength: 3,
            Defense: 6,
            Resistance: 13,
            Dexterity: 8,
            Speed: 9,
            Constitution: 7,
            Intelligence: 13,
            Wisdom: 17,
            Charisma: 12
        )
    );
}