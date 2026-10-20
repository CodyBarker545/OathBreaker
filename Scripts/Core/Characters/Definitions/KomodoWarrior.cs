namespace Oathbreakers.Core.Characters.Definitions;

public static class KomodoWarrior
{
    public static CharacterDefinition Definition => new(
        Id: "komodo_warrior",

        Name: "Komodo Warrior",

        Description: "A powerful reptilian warrior specializing in melee combat.",

        BaseStats: new CharacterStats(
            MaxHealth: 46,
            Strength: 15,
            Defense: 12,
            Resistance: 8,
            Dexterity: 10,
            Speed: 10,
            Constitution: 14,
            Intelligence: 3,
            Wisdom: 5,
            Charisma: 7
            )
        );
}
