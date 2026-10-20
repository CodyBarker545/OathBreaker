using Xunit;
using Oathbreakers.Core.Characters;

namespace Oathbreakers.Tests.Characters;

public class CharacterFactoryTests
{
    [Theory]
    [InlineData("komodo_warrior")]
    [InlineData("shadow_ninja")]
    [InlineData("assassin")]
    [InlineData("healer")]
    [InlineData("dark_mage")]
    [InlineData("iron_guardian")]
    
    public void Factory_CreatesAllCharacters(string characterId)
    {
        // Arrange
        var definition = CharacterRegistry.GetCharacter(characterId);

        Assert.NotNull(definition);

        // Act
        var character = CharacterFactory.Create(
            definition,
            instanceId: $"player1_{characterId}",
            teamId: 1
        );

        // Assert
        Assert.NotNull(character);
        Assert.Equal(definition.Name, character.Name);
        Assert.Equal(definition.BaseStats.MaxHealth, character.CurrentHealth);
        Assert.Equal(1, character.TeamId);
    }

    [Fact]
    public void Factory_CreatesIndependentCharacters()
    {
        // Arrange
        var definition = CharacterRegistry.GetCharacter("komodo_warrior");

        Assert.NotNull(definition);

        var warrior1 = CharacterFactory.Create(
            definition,
            "player1_komodo",
            1
        );

        var warrior2 = CharacterFactory.Create(
            definition,
            "player2_komodo",
            2
        );

        // Act
        warrior1.TakeDamage(20);

        // Assert
        Assert.Equal(26, warrior1.CurrentHealth);
        Assert.Equal(46, warrior2.CurrentHealth);
    }

    [Fact]
    public void Factory_AssignsCorrectTeamId()
    {
        var definition = CharacterRegistry.GetCharacter("assassin");

        Assert.NotNull(definition);

        var assassin = CharacterFactory.Create(
            definition,
            "player2_assassin",
            2
        );

        Assert.Equal(2, assassin.TeamId);
    }

    [Fact]
    public void Factory_AssignsUniqueInstanceIds()
    {
        var definition = CharacterRegistry.GetCharacter("assassin");

        Assert.NotNull(definition);

        var assassin1 = CharacterFactory.Create(
            definition,
            "assassin_001",
            1
        );

        var assassin2 = CharacterFactory.Create(
            definition,
            "assassin_002",
            2
        );

        Assert.NotEqual(assassin1.Id, assassin2.Id);
    }

    [Fact]
    public void Factory_NewCharacterStartsAtFullHealth()
    {
        var definition = CharacterRegistry.GetCharacter("iron_guardian");

        Assert.NotNull(definition);

        var guardian = CharacterFactory.Create(
            definition,
            "guardian_001",
            1
        );

        Assert.Equal(
            guardian.BaseStats.MaxHealth,
            guardian.CurrentHealth
        );
    }
}