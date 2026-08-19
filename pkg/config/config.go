package config

import (
	"os"
	"gopkg.in/yaml.v3"
)

type Config struct {
	Server struct {
		Port		string `yaml:"port"`
		SSHKeyPath  string `yaml:"ssh_key_path"`
	} `yaml:"server"`

	PythonVFS struct {
		Address		string `yaml:"address"`
		AuthToken	string `yaml:"auth_token"`
	} `yaml:"python_vfs"`

	Telemetry struct {
		ClickHouseURL string `yaml:"clickhouse_url"`
		Password	  string `yaml:"password"`
	} `yaml:"telemetry"`
	
	AIFallback struct {
		APIKey string `yaml:"api_key"`
	} `yaml:"ai_fallback"`
}

var AppConfig *Config

func LoadConfig(filePath string) error {
	file, err := os.ReadFile(filePath)
	if err != nil {
		return err
	}

	AppConfig = &Config{}
	err = yaml.Unmarshal(file, AppConfig)
	if err != nil {
		return err
	}
	return nil
}