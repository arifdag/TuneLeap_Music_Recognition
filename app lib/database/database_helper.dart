import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';

// --- Model Class for User Settings ---

class UserSetting {
  final String settingKey;
  String settingValue;

  UserSetting({required this.settingKey, required this.settingValue});

  Map<String, dynamic> toMap() {
    return {
      'settingKey': settingKey,
      'settingValue': settingValue,
    };
  }

  factory UserSetting.fromMap(Map<String, dynamic> map) {
    return UserSetting(
      settingKey: map['settingKey'],
      settingValue: map['settingValue'],
    );
  }
}

// --- Database Helper Class ---

class DatabaseHelper {
  static final DatabaseHelper _instance = DatabaseHelper._internal();
  factory DatabaseHelper() => _instance;
  DatabaseHelper._internal();

  static Database? _database;

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB();
    return _database!;
  }

  Future<Database> _initDB() async {
    Directory documentsDirectory = await getApplicationDocumentsDirectory();
    String path = join(documentsDirectory.path, 'flutter_music_app_local_settings.db'); // Changed DB name slightly
    return await openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
    );
  }

  Future _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE UserSettings (
        settingKey TEXT PRIMARY KEY,
        settingValue TEXT NOT NULL
      )
    ''');
  }


  // --- UserSettings CRUD ---
  Future<int> insertSetting(UserSetting setting) async {
    final db = await database;
    return await db.insert('UserSettings', setting.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<UserSetting?> getSetting(String key) async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'UserSettings',
      where: 'settingKey = ?',
      whereArgs: [key],
    );
    if (maps.isNotEmpty) {
      return UserSetting.fromMap(maps.first);
    }
    return null;
  }

  Future<List<UserSetting>> getAllSettings() async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query('UserSettings');
    return List.generate(maps.length, (i) {
      return UserSetting.fromMap(maps[i]);
    });
  }

  Future<int> updateSetting(UserSetting setting) async {
    final db = await database;
    return await db.update(
      'UserSettings',
      setting.toMap(),
      where: 'settingKey = ?',
      whereArgs: [setting.settingKey],
    );
  }

  Future<int> deleteSetting(String key) async {
    final db = await database;
    return await db.delete(
      'UserSettings',
      where: 'settingKey = ?',
      whereArgs: [key],
    );
  }

  Future<int> clearAllSettings() async {
    final db = await database;
    return await db.delete('UserSettings');
  }

  // Helper to close the database
  Future close() async {
    final db = await database;
    db.close();
    _database = null; // So it can be reopened if needed
  }
}