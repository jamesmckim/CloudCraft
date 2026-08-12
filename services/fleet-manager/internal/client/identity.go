package client

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"time"
)

type IdentityClient struct {
	BaseURL    string
	HTTPClient *http.Client
}

func NewIdentityClient(baseURL string) *IdentityClient {
	return &IdentityClient{
		BaseURL: baseURL,
		HTTPClient: &http.Client{
			Timeout: 10 * time.Second, // Prevent hanging requests
		},
	}
}

// GetUserCredits fetches the user's balance, mimicking the original httpx behavior.
func (c *IdentityClient) GetUserCredits(ctx context.Context, userID string) (float64, error) {
	url := fmt.Sprintf("%s/users/%s/credits", c.BaseURL, userID)

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return 0, fmt.Errorf("failed to create request: %v", err)
	}

	req.Header.Set("X-User-ID", userID)

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return 0, errors.New("identity service is currently unavailable")
	}
	defer resp.Body.Close()

	switch resp.StatusCode {
	case http.StatusOK:
		var data struct {
			Credits float64 `json:"credits"`
		}
		if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
			return 0, errors.New("failed to decode identity response")
		}
		return data.Credits, nil

	case http.StatusNotFound:
		return 0, errors.New("user not found in Identity Service")
	case http.StatusUnauthorized:
		return 0, errors.New("internal Auth Error: Missing X-User-ID header")
	default:
		return 0, fmt.Errorf("identity service returned unexpected status: %d", resp.StatusCode)
	}
}