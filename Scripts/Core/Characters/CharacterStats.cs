namespace PawnsOfDivinity.Core.Characters;

// Starting values for a character.
// A record gives these values a compact, immutable representation.

public sealed record CharacterStats(
    int MaxHealth,
    int Strength,
    int Defense,
    int Resistance,
    int Dexterity,
    int Speed,
    int Constitution,
    int Intelligence,
    int Wisdom,
    int Charisma);

