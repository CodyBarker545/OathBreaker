namespace PawnsOfDivinity.Core.Characters;

public static class CharacterFactory
{
    public static Character Create(
        CharacterDefinition definition,
        string instanceId,
        int teamId
    )
    {
        return new Character(
            id: instanceId,
            name: definition.Name,
            teamId: teamId,
            baseStats: definition.BaseStats
        );
    }
}