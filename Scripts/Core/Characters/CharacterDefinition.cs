namespace Oathbreakers.Core.Characters;

public record CharacterDefinition(
    string Id,
    string Name,
    string Description,
    CharacterStats BaseStats
);