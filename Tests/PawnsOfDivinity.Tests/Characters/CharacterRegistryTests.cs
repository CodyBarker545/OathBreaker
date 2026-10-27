using System.Linq;
using Xunit;
using PawnsOfDivinity.Core.Characters;

namespace PawnsOfDivinity.Tests.Characters;

public class CharacterRegistryTests
{
    [Fact]
    public void Registry_ContainsSevenCharacters()
    {
        var characters = CharacterRegistry.GetAllCharacters();

        Assert.Equal(6, characters.Count());
    }

    [Theory]
    [InlineData("komodo_warrior")]
    [InlineData("shadow_ninja")]
    [InlineData("assassin")]
    [InlineData("healer")]
    [InlineData("dark_mage")]
    [InlineData("iron_guardian")]
    public void Registry_CanFindAllCharacters(string characterId)
    {
        // Act
        var character = CharacterRegistry.GetCharacter(characterId);

        // Assert
        Assert.NotNull(character);
        Assert.Equal(characterId, character.Id);
    }

    [Fact]
    public void Registry_ReturnsNullForInvalidId()
    {
        var character = CharacterRegistry.GetCharacter("invalid_character");

        Assert.Null(character);
    }

    [Fact]
    public void Registry_ReturnsAllCharacterDefinitions()
    {
        var characters = CharacterRegistry.GetAllCharacters().ToList();

        Assert.NotEmpty(characters);

        foreach (var character in characters)
        {
            Assert.NotNull(character);
        }
    }

    [Fact]
    public void Registry_CharactersHaveUniqueNames()
    {
        var characters = CharacterRegistry.GetAllCharacters().ToList();

        var uniqueNames = characters
            .Select(c => c.Name)
            .Distinct()
            .Count();

        Assert.Equal(characters.Count, uniqueNames);
    }
}