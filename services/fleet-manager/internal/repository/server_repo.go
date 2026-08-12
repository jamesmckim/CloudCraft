package repository

import (
	"context"

	"fleet-manager/internal/model"
	"gorm.io/gorm"
)

type ServerRepository struct {
	db *gorm.DB
}

func NewServerRepository(db *gorm.DB) *ServerRepository {
	return &ServerRepository{db: db}
}

func (r *ServerRepository) GetByOwner(ctx context.Context, ownerID string) ([]*model.Server, error) {
	var servers []*model.Server
	err := r.db.WithContext(ctx).Where("owner_id = ?", ownerID).Find(&servers).Error
	return servers, err
}

func (r *ServerRepository) Get(ctx context.Context, id string) (*model.Server, error) {
	var server model.Server
	err := r.db.WithContext(ctx).First(&server, "id = ?", id).Error
	if err != nil {
		return nil, err
	}
	return &server, nil
}

func (r *ServerRepository) Create(ctx context.Context, server *model.Server) error {
	return r.db.WithContext(ctx).Create(server).Error
}

func (r *ServerRepository) UpdateActivePod(ctx context.Context, id string, podName *string) error {
	return r.db.WithContext(ctx).Model(&model.Server{}).Where("id = ?", id).Update("active_pod_name", podName).Error
}