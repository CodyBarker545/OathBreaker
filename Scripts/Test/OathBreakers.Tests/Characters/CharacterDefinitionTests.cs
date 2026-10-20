using System;
using System.Linq;
using Xunit;
using Oathbreakers.Core.Characters;
using Oathbreakers.Core.Characters.Definitions;

namespace Oathbreakers.Tests.Characters;

public class CharacterDefinitionTests
{
    // Test 1: Every character has valid statistics

    [Fact]
    public void AllCharacters_HaveValidStats()
    {
        // Arrange
        var characters = CharacterRegistry.GetAllCharacters();

        // Act & Assert
        foreach (var character in characters)
        {
            var stats = character.BaseStats;

            Assert.True(stats.MaxHealth > 0);
            Assert.True(stats.Strength >= 0);
            Assert.True(stats.Defense >= 0);
            Assert.True(stats.Resistance >= 0);
            Assert.True(stats.Dexterity >= 0);
            Assert.True(stats.Speed >= 0);
            Assert.True(stats.Constitution >= 0);
            Assert.True(stats.Intelligence >= 0);
            Assert.True(stats.Wisdom >= 0);
            Assert.True(stats.Charisma >= 0);
        }
    }

    // Test 2: Every character has an ID and name

    [Fact]
    public void AllCharacters_HaveValidIdentity()
    {
        foreach (var character in CharacterRegistry.GetAllCharacters())
        {
            Assert.False(string.IsNullOrWhiteSpace(character.Id));
            Assert.False(string.IsNullOrWhiteSpace(character.Name));
            Assert.False(string.IsNullOrWhiteSpace(character.Description));
        }
    }

    // Test 3: Every character has a unique ID

    [Fact]
    public void AllCharacters_HaveUniqueIds()
    {
        var characters = CharacterRegistry.GetAllCharacters().ToList();

        var uniqueIds = characters
            .Select(character => character.Id)
            .Distinct()
            .Count();

        Assert.Equal(characters.Count, uniqueIds);
    }

    // Test 4: Check intended character health

    [Theory]
    [InlineData("komodo_warrior", 46)]
    [InlineData("shadow_ninja", 32)]
    [InlineData("assassin", 30)]
    [InlineData("healer", 34)]
    [InlineData("dark_mage", 33)]
    [InlineData("iron_guardian", 58)]
    public void Character_HasCorrectMaxHealth(
        string characterId,
        int expectedHealth)
    {
        // Arrange
        var character = CharacterRegistry.GetCharacter(characterId);

        // Assert
        Assert.NotNull(character);

        Assert.Equal(
            expectedHealth,
            character.BaseStats.MaxHealth
        );
    }

    // Test 5: Verify expected Strength

    [Theory]
    [InlineData("komodo_warrior", 15)]
    [InlineData("shadow_ninja", 12)]
    [InlineData("assassin", 16)]
    [InlineData("healer", 3)]
    [InlineData("dark_mage", 2)]
    [InlineData("iron_guardian", 12)]
    public void Character_HasCorrectStrength(
        string characterId,
        int expectedStrength)
    {
        var character = CharacterRegistry.GetCharacter(characterId);

        Assert.NotNull(character);

        Assert.Equal(
            expectedStrength,
            character.BaseStats.Strength
        );
    }
}