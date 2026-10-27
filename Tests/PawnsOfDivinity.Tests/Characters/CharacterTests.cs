using System;
using PawnsOfDivinity.Core.Characters;
using Xunit;

namespace PawnsOfDivinity.Tests.Characters;

/// <summary>
/// Unit tests for the Character class.
///
/// Tests character creation, damage, healing,
/// defeat states, and turn activation.
///
/// Each test creates its own character to ensure
/// tests remain independent.
/// </summary>
public class CharacterTests
{
    // =========================================================
    // TEST DATA
    // =========================================================

    private const int MaxHealth = 46;

    /// <summary>
    /// Creates a standard Komodo Warrior for testing.
    ///
    /// Using a helper avoids repeating character creation
    /// throughout the test suite.
    /// </summary>
    private static Character CreateTestWarrior()
    {
        var stats = new CharacterStats(
            MaxHealth: MaxHealth,
            Strength: 15,
            Defense: 12,
            Resistance: 8,
            Dexterity: 14,
            Speed: 10,
            Constitution: 9,
            Intelligence: 11,
            Wisdom: 10,
            Charisma: 8
        );

        return new Character(
            id: "warrior-1",
            name: "Komodo Warrior",
            teamId: 1,
            baseStats: stats
        );
    }

    // =========================================================
    // CHARACTER CREATION TESTS
    // =========================================================

    [Fact]
    public void Constructor_ValidStats_StartsAtMaximumHealth()
    {
        // Arrange & Act
        var warrior = CreateTestWarrior();

        // Assert
        Assert.Equal(MaxHealth, warrior.CurrentHealth);
    }

    [Fact]
    public void Constructor_ValidStats_CharacterIsNotDefeated()
    {
        // Arrange & Act
        var warrior = CreateTestWarrior();

        // Assert
        Assert.False(warrior.IsDefeated);
    }

    [Fact]
    public void Constructor_ValidStats_PreservesCharacterStats()
    {
        // Arrange & Act
        var warrior = CreateTestWarrior();

        // Assert
        Assert.Equal(15, warrior.BaseStats.Strength);
        Assert.Equal(12, warrior.BaseStats.Defense);
        Assert.Equal(8, warrior.BaseStats.Resistance);
        Assert.Equal(14, warrior.BaseStats.Dexterity);
        Assert.Equal(10, warrior.BaseStats.Speed);
    }

    // =========================================================
    // DAMAGE TESTS
    // =========================================================

    [Fact]
    public void TakeDamage_ValidAmount_ReducesHealth()
    {
        // Arrange
        var warrior = CreateTestWarrior();

        // Act
        warrior.TakeDamage(15);

        // Assert
        Assert.Equal(31, warrior.CurrentHealth);
        Assert.False(warrior.IsDefeated);
    }

    [Fact]
    public void TakeDamage_ExceedsCurrentHealth_HealthStopsAtZero()
    {
        // Arrange
        var warrior = CreateTestWarrior();

        // Act
        warrior.TakeDamage(100);

        // Assert
        Assert.Equal(0, warrior.CurrentHealth);
        Assert.True(warrior.IsDefeated);
    }

    [Fact]
    public void TakeDamage_ExactlyCurrentHealth_CharacterIsDefeated()
    {
        // Arrange
        var warrior = CreateTestWarrior();

        // Act
        warrior.TakeDamage(MaxHealth);

        // Assert
        Assert.Equal(0, warrior.CurrentHealth);
        Assert.True(warrior.IsDefeated);
    }

    [Fact]
    public void TakeDamage_NegativeAmount_ThrowsArgumentOutOfRangeException()
    {
        // Arrange
        var warrior = CreateTestWarrior();

        // Act
        Action action = () => warrior.TakeDamage(-10);

        // Assert
        Assert.Throws<ArgumentOutOfRangeException>(action);

        Assert.Equal(MaxHealth, warrior.CurrentHealth);
    }

    [Fact]
    public void TakeDamage_ZeroAmount_DoesNotChangeHealth()
    {
        // Arrange
        var warrior = CreateTestWarrior();

        // Act
        warrior.TakeDamage(0);

        // Assert
        Assert.Equal(MaxHealth, warrior.CurrentHealth);
    }

    [Theory]
    [InlineData(0, 46)]
    [InlineData(5, 41)]
    [InlineData(10, 36)]
    [InlineData(20, 26)]
    [InlineData(30, 16)]
    [InlineData(46, 0)]
    [InlineData(100, 0)]
    public void TakeDamage_VariousAmounts_ProducesExpectedHealth(
        int damage,
        int expectedHealth)
    {
        // Arrange
        var warrior = CreateTestWarrior();

        // Act
        warrior.TakeDamage(damage);

        // Assert
        Assert.Equal(expectedHealth, warrior.CurrentHealth);
    }

    // =========================================================
    // HEALING TESTS
    // =========================================================

    [Fact]
    public void Heal_ValidAmount_RestoresHealth()
    {
        // Arrange
        var warrior = CreateTestWarrior();

        warrior.TakeDamage(20);

        // Act
        int restored = warrior.Heal(10);

        // Assert
        Assert.Equal(36, warrior.CurrentHealth);
        Assert.Equal(10, restored);
    }

    [Fact]
    public void Heal_ExceedsMissingHealth_CapsAtMaximumHealth()
    {
        // Arrange
        var warrior = CreateTestWarrior();

        warrior.TakeDamage(6);

        // Act
        int restored = warrior.Heal(20);

        // Assert
        Assert.Equal(MaxHealth, warrior.CurrentHealth);
        Assert.Equal(6, restored);
    }

    [Fact]
    public void Heal_AtMaximumHealth_RestoresNothing()
    {
        // Arrange
        var warrior = CreateTestWarrior();

        // Act
        int restored = warrior.Heal(20);

        // Assert
        Assert.Equal(MaxHealth, warrior.CurrentHealth);
        Assert.Equal(0, restored);
    }

    [Fact]
    public void Heal_NegativeAmount_ThrowsArgumentOutOfRangeException()
    {
        // Arrange
        var warrior = CreateTestWarrior();

        // Act
        Action action = () => warrior.Heal(-5);

        // Assert
        Assert.Throws<ArgumentOutOfRangeException>(action);
    }

    [Fact]
    public void Heal_DefeatedCharacter_DoesNotRevive()
    {
        // Arrange
        var warrior = CreateTestWarrior();

        warrior.TakeDamage(100);

        // Act
        int restored = warrior.Heal(20);

        // Assert
        Assert.Equal(0, warrior.CurrentHealth);
        Assert.Equal(0, restored);
        Assert.True(warrior.IsDefeated);
    }

    [Theory]
    [InlineData(10, 5, 41)]
    [InlineData(20, 10, 36)]
    [InlineData(30, 20, 36)]
    [InlineData(40, 50, 46)]
    public void Heal_VariousAmounts_ProducesExpectedHealth(
        int damage,
        int healing,
        int expectedHealth)
    {
        // Arrange
        var warrior = CreateTestWarrior();

        warrior.TakeDamage(damage);

        // Act
        warrior.Heal(healing);

        // Assert
        Assert.Equal(expectedHealth, warrior.CurrentHealth);
    }

    // =========================================================
    // DEFEAT TESTS
    // =========================================================

    [Fact]
    public void IsDefeated_WhenHealthIsAboveZero_ReturnsFalse()
    {
        // Arrange
        var warrior = CreateTestWarrior();

        warrior.TakeDamage(45);

        // Act
        bool defeated = warrior.IsDefeated;

        // Assert
        Assert.False(defeated);
        Assert.Equal(1, warrior.CurrentHealth);
    }

    [Fact]
    public void IsDefeated_WhenHealthReachesZero_ReturnsTrue()
    {
        // Arrange
        var warrior = CreateTestWarrior();

        // Act
        warrior.TakeDamage(46);

        // Assert
        Assert.True(warrior.IsDefeated);
    }

    // =========================================================
    // TURN ACTIVATION TESTS
    // =========================================================

    [Fact]
    public void Constructor_NewCharacter_HasNotActed()
    {
        // Arrange & Act
        var warrior = CreateTestWarrior();

        // Assert
        Assert.False(warrior.HasActedThisRound);
    }

    [Fact]
    public void EndActivation_ReadyCharacter_MarksAsActed()
    {
        // Arrange
        var warrior = CreateTestWarrior();

        // Act
        warrior.EndActivation();

        // Assert
        Assert.True(warrior.HasActedThisRound);
    }
}