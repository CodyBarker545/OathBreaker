using Oathbreakers.Core.Characters;

namespace Oathbreakers.Core.Characters.Definitions;

public static class IronGuardian
{
    public static CharacterDefinition Definition => new(
        Id: "iron_guardian",

        Name: "Iron Guardian",

        Description: "An armored juggernaut who withstands powerful attacks and protects allies.",

        BaseStats: new CharacterStats(
            MaxHealth: 58,
            Strength: 12,
            Defense: 19,
            Resistance: 6,
            Dexterity: 7,
            Speed: 5,
            Constitution: 18,
            Intelligence: 0,
            Wisdom: 7,
            Charisma: 10
        )
    );
}