using Oathbreakers.Core.Characters;

namespace Oathbreakers.Core.Characters.Definitions;

public static class ShadowNinja
{
    public static CharacterDefinition Definition => new(
        Id: "shadow_ninja",

        Name: "Shadow Ninja",

        Description: "A mysterious ninja who uses speed and deception to outmaneuver enemies.",

        BaseStats: new CharacterStats(
            MaxHealth: 32,
            Strength: 12,
            Defense: 6,
            Resistance: 7,
            Dexterity: 17,
            Speed: 18,
            Constitution: 7,
            Intelligence: 0,
            Wisdom: 8,
            Charisma: 6
        )
    );
}