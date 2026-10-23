using System;

namespace PawnsOfDivinity.Core.Characters;

public class Character
{
    //Identity 
    public string Id {get; }
    public string Name {get; }
    public int TeamId {get; }

    // Starting stats for a character.
    public CharacterStats BaseStats {get; }

    // Changing battle state
    public int CurrentHealth {get; private set; }
    public bool HasActedThisRound {get; private set; }
    public bool IsDefeated => CurrentHealth == 0; 

    public bool CanAct => !HasActedThisRound && !IsDefeated;

    public Character(
        string id,
        string name,
        int teamId,
        CharacterStats baseStats)
    {
        if (string.IsNullOrWhiteSpace(id))
            throw new ArgumentException("An ID is required.", nameof(id));

        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("A name is required.", nameof(name));

        ArgumentNullException.ThrowIfNull(baseStats);

        if (baseStats.MaxHealth <= 0   ||
            baseStats.Strength < 0     ||
            baseStats.Defense < 0      ||
            baseStats.Resistance < 0   ||
            baseStats.Dexterity < 0    ||
            baseStats.Constitution < 0 ||
            baseStats.Intelligence < 0 ||
            baseStats.Wisdom < 0       ||
            baseStats.Charisma < 0)
        {
            throw new ArgumentException(
                "Health must be positive and other stats cannot be negative.",
                nameof(baseStats));
        }

        Id = id;
        Name = name;
        TeamId = teamId;
        BaseStats = baseStats;
        CurrentHealth = baseStats.MaxHealth;
    }

    // Receive damage already calculated by the combat system.
    public int TakeDamage(int damage)
    {
        if (damage < 0)
            throw new ArgumentOutOfRangeException("Damage cannot be negative.", nameof(damage));
        int damageTaken = Math.Min(damage, CurrentHealth);
        CurrentHealth -= damageTaken;  

        return damageTaken;
    }

    /// <summary>
    /// Restores health to a living character.
    /// Healing cannot exceed maximum health.
    /// Defeated characters cannot be revived through normal healing.
    /// </summary>
    /// <param name="amount">Amount of healing requested.</param>
    /// <returns>Actual amount of health restored.</returns>
    public int Heal(int amount)
    {
        // Reject invalid healing values.
        if (amount < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(amount),
                "Healing cannot be negative."
            );
        }

        // Defeated characters cannot receive normal healing.
        if (IsDefeated)
        {
            return 0;
        }

        // Calculate the actual amount of healing.
        int healthRestored = Math.Min(
            amount,
            BaseStats.MaxHealth - CurrentHealth
        );

        // Restore health.
        CurrentHealth += healthRestored;

        // Return actual health restored.
        return healthRestored;
}

    public void EndActivation()
    {
        HasActedThisRound = true;
    }
    public void ResetActivation()
    {
        HasActedThisRound = false;
    }
}

