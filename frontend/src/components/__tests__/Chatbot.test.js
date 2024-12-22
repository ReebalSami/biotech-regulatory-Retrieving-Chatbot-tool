import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material';
import Chatbot from '../Chatbot';

// Mock fetch globally
global.fetch = jest.fn();

const theme = createTheme();

const renderChatbot = () => {
  return render(
    <ThemeProvider theme={theme}>
      <Chatbot />
    </ThemeProvider>
  );
};

describe('Chatbot Component', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('renders chatbot component correctly', () => {
    renderChatbot();
    expect(screen.getByPlaceholderText(/Type your message/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('displays welcome message on initial render', () => {
    renderChatbot();
    expect(screen.getByText(/Hello! I'm your biotech regulatory assistant/i)).toBeInTheDocument();
  });

  it('handles user input correctly', async () => {
    renderChatbot();
    const input = screen.getByPlaceholderText(/Type your message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    await userEvent.type(input, 'Test message');
    expect(input).toHaveValue('Test message');

    fireEvent.click(sendButton);
    expect(input).toHaveValue(''); // Input should be cleared after sending
  });

  it('displays user message in chat', async () => {
    renderChatbot();
    const input = screen.getByPlaceholderText(/Type your message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    await userEvent.type(input, 'Test message');
    fireEvent.click(sendButton);

    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('handles API response correctly', async () => {
    const mockResponse = { response: 'API response' };
    fetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })
    );

    renderChatbot();
    const input = screen.getByPlaceholderText(/Type your message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    await userEvent.type(input, 'Test message');
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('API response')).toBeInTheDocument();
    });
  });

  it('handles API error correctly', async () => {
    fetch.mockImplementationOnce(() =>
      Promise.reject(new Error('API Error'))
    );

    renderChatbot();
    const input = screen.getByPlaceholderText(/Type your message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    await userEvent.type(input, 'Test message');
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/Error: Could not get response/i)).toBeInTheDocument();
    });
  });

  it('shows loading state while waiting for response', async () => {
    fetch.mockImplementationOnce(() =>
      new Promise(resolve =>
        setTimeout(() =>
          resolve({
            ok: true,
            json: () => Promise.resolve({ response: 'Delayed response' }),
          }),
          1000
        )
      )
    );

    renderChatbot();
    const input = screen.getByPlaceholderText(/Type your message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    await userEvent.type(input, 'Test message');
    fireEvent.click(sendButton);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles empty input correctly', async () => {
    renderChatbot();
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.click(sendButton);
    expect(fetch).not.toHaveBeenCalled();
  });

  it('handles enter key press correctly', async () => {
    renderChatbot();
    const input = screen.getByPlaceholderText(/Type your message/i);

    await userEvent.type(input, 'Test message{enter}');
    expect(input).toHaveValue(''); // Input should be cleared after sending
  });

  it('maintains chat history correctly', async () => {
    const mockResponses = [
      { response: 'First response' },
      { response: 'Second response' },
    ];

    fetch
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockResponses[0]),
        })
      )
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockResponses[1]),
        })
      );

    renderChatbot();
    const input = screen.getByPlaceholderText(/Type your message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    // First message
    await userEvent.type(input, 'First message');
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('First response')).toBeInTheDocument();
    });

    // Second message
    await userEvent.type(input, 'Second message');
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('First response')).toBeInTheDocument();
      expect(screen.getByText('Second response')).toBeInTheDocument();
    });
  });
});
