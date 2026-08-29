package telemetry

import (
	"encoding/json"
	"sync"
)

type SSEEvent struct {
	Type string		 `json:"type"`
	Data interface{} `json:"data"`
}

type Broker struct {
	clients map[chan []byte]bool
	entering chan chan []byte
	leaving	 chan chan []byte
	messages chan []byte
}

var (
	GlobalBroker *Broker
	once		 sync.Once
)

func GetBroker() *Broker {
	once.Do(func() {
		GlobalBroker = &Broker{
			clients:	make(map[chan []byte]bool),
			entering: 	make(chan chan []byte),
			leaving: 	make(chan chan []byte),
			messages:	make(chan []byte, 100),
		}
		go GlobalBroker.listen()
	})
	return GlobalBroker
}

func (b *Broker) listen() {
	for {
		select {
		case s := <-b.entering:
			b.clients[s] = true
		case s := <-b.leaving:
			delete(b.clients, s)
			close(s)
		case msg := <-b.messages:
			for s := range b.clients {
				select {
				case s <- msg:
				default:
				}
			}
		}
	}
}

func (b *Broker) Broadcast(eventType string, data interface{}) {
	event := SSEEvent{Type: eventType, Data: data}
	jsonData, err := json.Marshal(event)
	if err == nil {
		b.messages <- jsonData
	}
}

func (b *Broker) Subscribe() chan []byte {
	c := make(chan []byte, 10)
	b.entering <- c
	return c
}

func (b *Broker) Unsubscribe(c chan []byte) {
	b.leaving <- c
}