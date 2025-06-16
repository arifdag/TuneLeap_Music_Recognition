import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/api_config.dart';

enum AuthStatus {
  success,
  wrongCredentials,
  emailAlreadyExists,
  serverError,
  timeout,
  networkError,
  unknownError
}

class AuthResult {
  final AuthStatus status;
  final String message;

  AuthResult(this.status, this.message);
}

class AuthService {
  final Duration _timeoutDuration = Duration(seconds: 15);

  Future<AuthResult> register(String email, String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/auth/register'),
        headers: <String, String>{
          'Content-Type': 'application/json; charset=UTF-8',
        },
        body: jsonEncode(<String, String>{
          'email': email,
          'username': username,
          'password': password,
        }),
      ).timeout(_timeoutDuration);

      switch (response.statusCode) {
        case 201:
          return AuthResult(AuthStatus.success, 'Account created successfully!');
        case 400:
          // Parse error message from response
          try {
            final errorData = jsonDecode(response.body);
            if (errorData['detail'] != null) {
              final detail = errorData['detail'];
              if (detail.toString().toLowerCase().contains('email') && 
                  detail.toString().toLowerCase().contains('already')) {
                return AuthResult(AuthStatus.emailAlreadyExists, 'An account with this email already exists.');
              }
            }
          } catch (e) {
            // Fall through to default error
          }
          return AuthResult(AuthStatus.serverError, 'Invalid registration data. Please check your input.');
        case 422:
          return AuthResult(AuthStatus.serverError, 'Invalid email format or password requirements not met.');
        case 500:
          return AuthResult(AuthStatus.serverError, 'Server error occurred. Please try again later.');
        default:
          return AuthResult(AuthStatus.unknownError, 'Registration failed. Please try again.');
      }
    } on TimeoutException {
      return AuthResult(AuthStatus.timeout, 'Server is overloaded or temporarily unavailable. Please try again later.');
    } catch (e) {
      return AuthResult(AuthStatus.networkError, 'Network error. Please check your internet connection.');
    }
  }

  Future<AuthResult> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/auth/token'),
        headers: <String, String>{
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: {
          'username': email, // The backend expects the email in the username field for login
          'password': password,
        },
      ).timeout(_timeoutDuration);

      switch (response.statusCode) {
        case 200:
          final data = jsonDecode(response.body);
          print('Login successful: ${response.body}');
          if (data['access_token'] == null) {
            print('ERROR: No access_token in login response');
            return AuthResult(AuthStatus.serverError, 'Server error: Missing token in response');
          }
          
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('token', data['access_token']);
          print('Token saved to storage: ${data['access_token'].substring(0, 10)}...');
          return AuthResult(AuthStatus.success, 'Login successful!');
        case 400:
        case 401:
          return AuthResult(AuthStatus.wrongCredentials, 'Invalid email or password. Please try again.');
        case 422:
          return AuthResult(AuthStatus.serverError, 'Invalid login format. Please check your email and password.');
        case 500:
          return AuthResult(AuthStatus.serverError, 'Server error occurred. Please try again later.');
        default:
          return AuthResult(AuthStatus.unknownError, 'Login failed. Please try again.');
      }
    } on TimeoutException {
      return AuthResult(AuthStatus.timeout, 'Server is overloaded or temporarily unavailable. Please try again later.');
    } catch (e) {
      return AuthResult(AuthStatus.networkError, 'Network error. Please check your internet connection.');
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('token');
  }

  Future<bool> isLoggedIn() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    return token != null && token.isNotEmpty;
  }
  
  Future<bool> validateToken() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('token');
      
      if (token == null || token.isEmpty) {
        print('No token found in storage');
        return false;
      }
      
      print('Validating token: ${token.substring(0, 10)}...');
      
      final endpoint = '${ApiConfig.baseUrl}/auth/users/me';
      print('Token validation endpoint: $endpoint');
      
      // Make a request to the correct user validation endpoint
      final response = await http.get(
        Uri.parse(endpoint),
        headers: {
          'Authorization': 'Bearer $token',
        },
      ).timeout(_timeoutDuration);
      
      print('Token validation response: ${response.statusCode}');
      print('Response body: ${response.body}');
      
      if (response.statusCode == 200) {
        print('Token is valid');
        return true;
      } else {
        print('Token validation failed: ${response.statusCode}');
        if (response.statusCode == 401) {
          // Token is invalid or expired, clear it
          print('Token is invalid or expired, clearing it');
          await logout();
        }
        return false;
      }
    } catch (e) {
      print('Error validating token: $e');
      return false;
    }
  }
}