import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/recognition_history.dart';
import '../utils/api_config.dart';
import 'auth_service.dart';

class HistoryService {
  final AuthService _authService = AuthService();
  
  Future<String?> _getAuthToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token');
  }
  
  Future<bool> _ensureValidToken() async {
    // First check if user is logged in
    if (!await _authService.isLoggedIn()) {
      print('User is not logged in');
      return false;
    }
    
    print('User is logged in, validating token...');
    // Then validate token
    final isValid = await _authService.validateToken();
    print('Token validation result: $isValid');
    return isValid;
  }

  Future<bool> recordRecognitionEvent(int songId) async {
    try {
      // Ensure we have a valid token before proceeding
      if (!await _ensureValidToken()) {
        print('Cannot save history: No valid token');
        return false;
      }
      
      final token = await _getAuthToken();
      
      // The /me/history/ endpoint is at the root level, not under /auth
      final url = '${ApiConfig.baseUrl}/me/history/';
      print('Sending POST request to: $url');
      print('Request body: {"song_id": $songId}');
      
      // Print all songs that are successfully recognized to help debugging
      print('Trying to save song with ID: $songId to history');
      
      try {
        final response = await http.post(
          Uri.parse(url),
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
          body: jsonEncode({
            'song_id': songId,
            'client_info': 'Flutter Mobile App',
            'source': 'mobile_recognition'
          }),
        );
        
        // If we get a 500 error, try a simpler request with just the song_id
        if (response.statusCode == 500) {
          print('Got 500 error, trying simplified request...');
          final retryResponse = await http.post(
            Uri.parse(url),
            headers: {
              'Authorization': 'Bearer $token',
              'Content-Type': 'application/json',
            },
            body: jsonEncode({
              'song_id': songId,
            }),
          );
          
          print('Retry response code: ${retryResponse.statusCode}');
          print('Retry response body: ${retryResponse.body}');
          
          return retryResponse.statusCode == 201;
        }
        
        return response.statusCode == 201;
      } catch (e) {
        print('Exception during history API call: $e');
        return false; // Return false instead of Response object
      }
      
      // Note: Response handling is now done within the try/catch block above
    } catch (e) {
      print('Exception recording recognition event: $e');
      return false;
    }
  }

  Future<List<RecognitionHistory>> getHistoryList({int limit = 20, int skip = 0}) async {
    try {
      // Ensure we have a valid token before proceeding
      if (!await _ensureValidToken()) {
        print('Cannot get history: No valid token');
        return [];
      }
      
      final token = await _getAuthToken();
      final url = '${ApiConfig.baseUrl}/me/history/?skip=$skip&limit=$limit';
      print('Fetching history from: $url');
      
      final response = await http.get(
        Uri.parse(url),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );
      
      print('History list response status: ${response.statusCode}');
      
      // Print full response for debugging
      print('===== FULL HISTORY RESPONSE START =====');
      print(response.body);
      print('===== FULL HISTORY RESPONSE END =====');
      
      if (response.statusCode == 200) {
        try {
          final List<dynamic> data = jsonDecode(response.body);
          print('Parsed ${data.length} history items');
          
          final items = data.map((item) => RecognitionHistory.fromJson(item)).toList();
          print('Converted to ${items.length} RecognitionHistory objects');
          return items;
        } catch (parseError) {
          print('Error parsing history data: $parseError');
          return [];
        }
      } else if (response.statusCode == 401) {
        print('Unauthorized: Token may be invalid');
        return [];
      } else if (response.statusCode == 500) {
        print('Server error when fetching history');
        return [];
      } else {
        print('Unexpected response code: ${response.statusCode}');
        return [];
      }
    } catch (e) {
      print('Exception getting history: $e');
      return [];
    }
  }

  Future<bool> deleteHistoryItem(int eventId) async {
    try {
      // Ensure we have a valid token before proceeding
      if (!await _ensureValidToken()) {
        print('Cannot delete history item: No valid token');
        return false;
      }
      
      final token = await _getAuthToken();
      
      final response = await http.delete(
        Uri.parse('${ApiConfig.baseUrl}/me/history/$eventId'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );
      
      return response.statusCode == 204;
    } catch (e) {
      print('Error deleting history item: $e');
      return false;
    }
  }
} 