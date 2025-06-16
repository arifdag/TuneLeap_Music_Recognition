class RecognitionHistory {
  final int id;
  final int songId;
  final String songTitle;
  final String artistName;
  final String? albumName;
  final String? albumImage;
  final DateTime recognizedAt;

  RecognitionHistory({
    required this.id,
    required this.songId,
    required this.songTitle,
    required this.artistName,
    this.albumName,
    this.albumImage,
    required this.recognizedAt,
  });

  static String _getSafePrint(dynamic value) {
    try {
      return value.toString();
    } catch (_) {
      return 'Unable to print value';
    }
  }

  factory RecognitionHistory.fromJson(Map<String, dynamic> json) {
    // Safe printing function
    void printSafe(String message) {
      print(message);
    }
    
    // Print the raw JSON to debug with full details
    printSafe('===== HISTORY ITEM JSON START =====');
    printSafe(_getSafePrint(json));
    printSafe('===== HISTORY ITEM JSON END =====');
    
    try {
      // Extract song information - several possible formats
      Map<String, dynamic> songData = {};
      
      // Format 1: Direct song fields
      if (json.containsKey('song_title') && json.containsKey('artist_name')) {
        printSafe('Format 1: Direct song fields found');
        return RecognitionHistory(
          id: json['id'] ?? 0,
          songId: json['song_id'] ?? 0,
          songTitle: json['song_title'] ?? 'Unknown Song',
          artistName: json['artist_name'] ?? 'Unknown Artist',
          albumName: json['album_name'],
          albumImage: json['album_image'],
          recognizedAt: json.containsKey('recognized_at') 
              ? DateTime.parse(json['recognized_at']) 
              : DateTime.now(),
        );
      }
      
      // Format 2: Nested song object
      if (json.containsKey('song') && json['song'] is Map) {
        printSafe('Format 2: Nested song object found');
        songData = json['song'] as Map<String, dynamic>;
        
        String songTitle = songData['title'] ?? 'Unknown Song';
        String artistName = 'Unknown Artist';
        String? albumName;
        String? albumImage;
        
        // Format 2.1: Artist directly in song object
        if (songData.containsKey('artist_name')) {
          printSafe('Format 2.1: Artist directly in song');
          artistName = songData['artist_name'] ?? artistName;
        }
        
        // Format 2.2: Nested artist object
        if (songData.containsKey('artist') && songData['artist'] is Map) {
          printSafe('Format 2.2: Nested artist object');
          final artistData = songData['artist'] as Map<String, dynamic>;
          if (artistData.containsKey('name')) {
            artistName = artistData['name'] ?? artistName;
          }
        }
        
        // Album handling
        if (songData.containsKey('album_name')) {
          albumName = songData['album_name'];
        }
        
        if (songData.containsKey('album_image')) {
          albumImage = songData['album_image'];
        }
        
        // Nested album object
        if (songData.containsKey('album') && songData['album'] is Map) {
          final albumData = songData['album'] as Map<String, dynamic>;
          if (albumData.containsKey('name')) {
            albumName = albumData['name'] ?? albumName;
          }
          if (albumData.containsKey('image')) {
            albumImage = albumData['image'] ?? albumImage;
          }
        }
        
        return RecognitionHistory(
          id: json['id'] ?? 0,
          songId: json['song_id'] ?? 0,
          songTitle: songTitle,
          artistName: artistName,
          albumName: albumName,
          albumImage: albumImage,
          recognizedAt: json.containsKey('recognized_at') 
              ? DateTime.parse(json['recognized_at']) 
              : DateTime.now(),
        );
      }
      
      // If we can't identify the format, use the fallback
      printSafe('Unknown format, using fallback parsing');
      
      // Try to extract values safely
      int id = 0;
      int songId = 0;
      String songTitle = 'Unknown Song';
      String artistName = 'Unknown Artist';
      String? albumName;
      String? albumImage;
      DateTime recognizedAt = DateTime.now();
      
      try {
        if (json.containsKey('id')) id = json['id'] as int;
        if (json.containsKey('song_id')) songId = json['song_id'] as int;
        
        // Try to find song title in various places
        if (json.containsKey('song_title')) {
          songTitle = json['song_title'] as String;
        } else if (json.containsKey('song') && json['song'] is Map) {
          final song = json['song'] as Map<String, dynamic>;
          if (song.containsKey('title')) songTitle = song['title'] as String;
        }
        
        // Try to find artist name in various places
        if (json.containsKey('artist_name')) {
          artistName = json['artist_name'] as String;
        } else if (json.containsKey('song') && json['song'] is Map) {
          final song = json['song'] as Map<String, dynamic>;
          if (song.containsKey('artist_name')) {
            artistName = song['artist_name'] as String;
          } else if (song.containsKey('artist') && song['artist'] is Map) {
            final artist = song['artist'] as Map<String, dynamic>;
            if (artist.containsKey('name')) artistName = artist['name'] as String;
          }
        }
        
        if (json.containsKey('recognized_at')) {
          recognizedAt = DateTime.parse(json['recognized_at']);
        }
      } catch (e) {
        printSafe('Error during fallback parsing: ${e.toString()}');
      }
      
      return RecognitionHistory(
        id: id,
        songId: songId,
        songTitle: songTitle,
        artistName: artistName,
        albumName: albumName,
        albumImage: albumImage,
        recognizedAt: recognizedAt,
      );
    } catch (e) {
      printSafe('Error parsing history item: ${e.toString()}');
      // Return a fallback item in case of parsing errors
      return RecognitionHistory(
        id: json.containsKey('id') ? (json['id'] as int? ?? 0) : 0,
        songId: json.containsKey('song_id') ? (json['song_id'] as int? ?? 0) : 0,
        songTitle: 'Error: Could not parse song',
        artistName: 'Unknown',
        recognizedAt: DateTime.now(),
      );
    }
  }
} 