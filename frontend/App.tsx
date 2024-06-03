import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, Button, ScrollView } from 'react-native';
import axios from 'axios';

export default function App() {
  const [userInput, setUserInput] = useState('');
  const [chatResponse, setChatResponse] = useState('');
  const [chatHistory, setChatHistory] = useState<string[]>([]);

  const handleChat = async () => {
    if (!userInput.trim()) return;

    try {
      const response = await axios.post('http://127.0.0.1:8000/chat', {
        user_input: userInput,
      });

      const responseData = response.data;
      if (responseData.response) {
        setChatHistory([...chatHistory, `You: ${userInput}`, `Bot: ${responseData.response}`]);
        setChatResponse(responseData.response);
      } else {
        setChatHistory([...chatHistory, `You: ${userInput}`, `Bot: Error: ${responseData.error}`]);
        setChatResponse(`Error: ${responseData.error}`);
      }
    } catch (error) {
      setChatHistory([...chatHistory, `You: ${userInput}`, `Bot: Error: ${error.message}`]);
      setChatResponse(`Error: ${error.message}`);
    }

    setUserInput('');
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Chatbot Interface</Text>
      <ScrollView style={styles.chatContainer}>
        {chatHistory.map((chat, index) => (
          <Text key={index} style={styles.chatText}>
            {chat}
          </Text>
        ))}
      </ScrollView>
      <TextInput
        style={styles.input}
        placeholder="Type your message..."
        value={userInput}
        onChangeText={setUserInput}
      />
      <Button title="Send" onPress={handleChat} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  chatContainer: {
    flex: 1,
    width: '100%',
    marginBottom: 20,
  },
  chatText: {
    fontSize: 16,
    marginBottom: 10,
  },
  input: {
    width: '100%',
    padding: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    marginBottom: 10,
    borderRadius: 5,
  },
});
