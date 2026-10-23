using System.Collections.Generic;
using PawnsOfDivinity.Core.Characters.Definitions;

namespace PawnsOfDivinity.Core.Characters;

public static class CharacterRegistry
{
    private static readonly Dictionary<string, CharacterDefinition> Characters = new()
    {
        { "komodo_warrior", KomodoWarrior.Definition },
        { "shadow_ninja", ShadowNinja.Definition },
        { "assassin", Assassin.Definition },
        { "healer", Healer.Definition },
        { "dark_mage", DarkMage.Definition },
        { "iron_guardian", IronGuardian.Definition }
    
    };

    public static CharacterDefinition? GetCharacter(string id)
    {
        return Characters.TryGetValue(id, out var character)
            ? character
            : null;
    }

    public static IEnumerable<CharacterDefinition> GetAllCharacters()
    {
        return Characters.Values;
    }
}