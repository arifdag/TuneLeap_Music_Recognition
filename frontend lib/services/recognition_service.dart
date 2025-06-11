import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/material.dart';
import '../utils/api_config.dart';
import 'history_service.dart';
import 'auth_service.dart';
import '../widgets/login_prompt_dialog.dart';

class RecognitionService {
  final AuthService _authService = AuthService();
  final HistoryService _historyService = HistoryService();
  
  Future<String?> _getAuthToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token');
  }

  Future<Map<String, dynamic>> recognizeAudio(File audioFile) async {
    try {
      final token = await _getAuthToken();
      
      // Create multipart request
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('${ApiConfig.baseUrl}/recognize/'),
      );

      // Add auth header if token exists
      if (token != null) {
        request.headers['Authorization'] = 'Bearer $token';
      }

      // Add audio file
      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          audioFile.path,
          filename: 'recording.wav',
        ),
      );

      // Send request
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 202) {
        // Task accepted, return task ID
        final data = json.decode(response.body);
        return {
          'status': 'accepted',
          'task_id': data['task_id'],
        };
      } else {
        return {
          'status': 'error',
          'message': 'Failed to start recognition: ${response.statusCode}',
        };
      }
    } catch (e) {
      return {
        'status': 'error',
        'message': 'Error recognizing audio: $e',
      };
    }
  }

  Future<Map<String, dynamic>> getRecognitionResult(String taskId) async {
    try {
      final token = await _getAuthToken();
      
      final headers = <String, String>{};
      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/recognize/result/$taskId'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        if (data['status'] == 'PENDING') {
          return {'status': 'pending'};
        } else if (data['status'] == 'FAILURE') {
          return {
            'status': 'error',
            'message': data['error'] ?? 'Recognition failed',
          };
        } else if (data['status'] == 'SUCCESS') {
          // Process successful recognition
          return {
            'status': 'success',
            'results': data['results'],
          };
        } else {
          // Handle other statuses
          return data;
        }
      } else if (response.statusCode == 404) {
        return {
          'status': 'no_match',
          'message': 'No match found',
        };
      } else {
        return {
          'status': 'error',
          'message': 'Failed to get result: ${response.statusCode}',
        };
      }
    } catch (e) {
      return {
        'status': 'error',
        'message': 'Error getting result: $e',
      };
    }
  }

  // Poll for recognition result
  Future<Map<String, dynamic>> pollForResult(String taskId, {Duration timeout = const Duration(seconds: 30), BuildContext? context}) async {
    final endTime = DateTime.now().add(timeout);
    
    while (DateTime.now().isBefore(endTime)) {
      final result = await getRecognitionResult(taskId);
      
      if (result['status'] != 'pending') {
        // Debug: Print full result to understand its structure
        print('Recognition result: ${result.toString()}');
        
        // If recognition was successful, record it to history
        if (result['status'] == 'success') {
          print('Recognition successful, checking for results...');
          if (result['results'] != null) {
            print('Results found: ${result['results'].length} items');
            if (result['results'].isNotEmpty) {
              // Get the first result (most likely match)
              final firstMatch = result['results'][0];
              print('First match: $firstMatch');
              
              if (firstMatch != null) {
                int? songId;
                // Check different possible formats for song_id
                if (firstMatch['song_id'] != null) {
                  songId = firstMatch['song_id'];
                } else if (firstMatch['id'] != null) {
                  songId = firstMatch['id'];
                }
                
                if (songId != null) {
                  print('Found song ID: $songId, saving to history...');
                              // For debugging purposes, try to save without showing login prompts
            final isLoggedIn = await _authService.isLoggedIn();
            print('User logged in status: $isLoggedIn');
            
            if (isLoggedIn) {
              // Try to save to history directly without showing prompts
              final saved = await _historyService.recordRecognitionEvent(songId);
              print('History saved: $saved');
            } else {
              print('User is not logged in, cannot save to history');
              // We'll implement the login prompt in a later version
              // after fixing the current token validation issues
            }
                } else {
                  print('ERROR: No song ID found in match: $firstMatch');
                }
              }
            } else {
              print('Results array is empty');
            }
          } else {
            print('No results array in response');
          }
        }
        return result;
      }
      
      // Wait before polling again
      await Future.delayed(const Duration(seconds: 1));
    }
    
    return {
      'status': 'error',
      'message': 'Recognition timeout',
    };
  }
} 