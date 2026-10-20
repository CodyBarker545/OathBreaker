using Oathbreakers.Core.Characters;

namespace Oathbreakers.Core.Characters.Definitions;

public static class DarkMage
{
    public static CharacterDefinition Definition => new(
        Id: "dark_mage",

        Name: "Dark Mage",

        Description: "A forbidden sorcerer who channels destructive shadow magic.",

        BaseStats: new CharacterStats(
            MaxHealth: 33,
            Strength: 2,
            Defense: 5,
            Resistance: 12,
            Dexterity: 12,
            Speed: 11,
            Constitution: 6,
            Intelligence: 17,
            Wisdom: 11,
            Charisma: 8
        )
    );
}