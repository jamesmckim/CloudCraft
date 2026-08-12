package model

import (
	"time"

	"gorm.io/gorm"
)

// Server represents a user's game server and its configurations.
type Server struct {
	ID            string                 `gorm:"primaryKey;type:varchar(255)"` // Logical server ID (UUID)
	OwnerID       string                 `gorm:"index;type:varchar(255)"`      // User ID from Identity Service
	GameID        string                 `gorm:"type:varchar(50)"`
	Config        map[string]interface{} `gorm:"type:json;serializer:json"`    // Game configs to enable redeployment
	ActivePodName *string                `gorm:"type:varchar(255)"`            // Nullable: Ephemeral Pod ID
	HourlyCost    float64                `gorm:"default:0.10"`
}

// IncidentReport tracks errors and AI/System recommendations.
type IncidentReport struct {
	ID             uint      `gorm:"primaryKey"`
	ServerID       string    `gorm:"index;type:varchar(255)"`
	ErrorLine      string    `gorm:"type:text"`
	Recommendation string    `gorm:"type:text"`
	CreatedAt      time.Time `gorm:"autoCreateTime"`
}

// AutoMigrate safely builds database tables.
func AutoMigrate(db *gorm.DB) error {
	return db.AutoMigrate(
		&Server{},
		&IncidentReport{},
	)
}