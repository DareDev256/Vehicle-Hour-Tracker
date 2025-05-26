import React, { useState } from 'react';
import { Clock, User, Car, Download, BarChart3, Play, Square } from 'lucide-react';

const DetailingWireframes = () => {
  const [currentScreen, setCurrentScreen] = useState('main');
  const [isTimerActive, setIsTimerActive] = useState(false);
  const [selectedDetailer, setSelectedDetailer] = useState('');
  const [editingEntry, setEditingEntry] = useState(null);
  const [draftEntry, setDraftEntry] = useState({});
  const [selectedEntries, setSelectedEntries] = useState([]);

  const mockData = [
    { id: 1, plate: 'ABC-123', type: 'Full Detail', advisor: 'Sarah M.', location: 'Bay 1', hours: '2.5', date: 'Today' },
    { id: 2, plate: 'XYZ-789', type: 'Interior', advisor: 'Mike R.', location: 'Bay 2', hours: '1.2', date: 'Today' },
    { id: 3, plate: 'DEF-456', type: 'Polish', advisor: 'Lisa K.', location: 'Bay 3', hours: '3.1', date: 'Yesterday' }
  ];

  const Screen = ({ title, children }) => (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-md mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-800">{title}</h2>
        <div className="flex gap-2">
          {['main', 'entry', 'log', 'dashboard'].map(screen => (
            <button
              key={screen}
              onClick={() => setCurrentScreen(screen)}
              className={`px-3 py-1 text-sm rounded ${
                currentScreen === screen 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
              }`}
            >
              {screen === 'main' ? 'Main' : screen === 'entry' ? 'Entry' : screen === 'log' ? 'Log' : 'Dashboard'}
            </button>
          ))}
        </div>
      </div>
      {children}
    </div>
  );

  const MainScreen = () => (
    <Screen title="Time Tracker">
      {/* Detailer Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <User className="inline w-4 h-4 mr-1" />
          Select Detailer
        </label>
        <select 
          value={selectedDetailer}
          onChange={(e) => setSelectedDetailer(e.target.value)}
          className="w-full p-3 border rounded-lg bg-gray-50"
        >
          <option value="">Choose detailer...</option>
          <option value="john">John Smith</option>
          <option value="maria">Maria Garcia</option>
          <option value="david">David Chen</option>
        </select>
      </div>

      {/* Quick Stats Widget */}
      <div className="bg-gradient-to-r from-blue-50 to-green-50 p-4 rounded-lg mb-4 border">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-medium text-gray-700">Today's Progress</h3>
          <span className="text-xs text-gray-500">Live Stats</span>
        </div>
        <div className="grid grid-cols-4 gap-2 text-center">
          <div>
            <div className="text-lg font-bold text-blue-600">4</div>
            <div className="text-xs text-gray-600">Cars</div>
          </div>
          <div>
            <div className="text-lg font-bold text-green-600">7.2</div>
            <div className="text-xs text-gray-600">Hours</div>
          </div>
          <div>
            <div className="text-lg font-bold text-orange-600">1.8</div>
            <div className="text-xs text-gray-600">Avg</div>
          </div>
          <div>
            <div className="text-lg font-bold text-purple-600">$340</div>
            <div className="text-xs text-gray-600">Value</div>
          </div>
        </div>
      </div>

      {/* New Entry Button */}
      <button 
        onClick={() => setCurrentScreen('entry')}
        className="w-full bg-blue-500 hover:bg-blue-600 text-white p-4 rounded-lg mb-4 flex items-center justify-center gap-2"
        disabled={!selectedDetailer}
      >
        <Car className="w-5 h-5" />
        Add New Entry
      </button>

      {/* View Toggle */}
      <div className="flex gap-2 mb-4">
        <button 
          onClick={() => setCurrentScreen('log')}
          className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 rounded flex items-center justify-center gap-1"
        >
          📋 View Full Log
        </button>
        <button 
          onClick={() => setCurrentScreen('entry')}
          className="bg-green-500 hover:bg-green-600 text-white px-3 py-2 rounded flex items-center gap-1"
        >
          📄 Duplicate Last
        </button>
        <button className="bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 rounded flex items-center justify-center gap-1">
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>

      {/* Recent Entries */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-3">
          <h3 className="font-medium text-gray-700">Recent Entries</h3>
          <select className="text-sm border rounded px-2 py-1">
            <option>Today</option>
            <option>This Week</option>
            <option>All Time</option>
          </select>
        </div>
        
        <div className="space-y-2">
          {mockData.map(entry => (
            <div key={entry.id} className="bg-gray-50 p-3 rounded flex justify-between items-center group hover:bg-gray-100">
              <div onClick={() => setEditingEntry(entry)} className="flex-1 cursor-pointer">
                <div className="font-medium">{entry.plate}</div>
                <div className="text-sm text-gray-600">{entry.type} • {entry.advisor}</div>
              </div>
              <div className="text-right">
                <div className={`font-bold ${parseFloat(entry.hours) > 3 ? 'text-red-600' : ''}`}>
                  {entry.hours}h
                </div>
                <div className="text-xs text-gray-500">{entry.location}</div>
                <button className="opacity-0 group-hover:opacity-100 text-xs text-blue-600 hover:underline">
                  Quick Edit
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="flex gap-2">
        <button 
          onClick={() => setCurrentScreen('dashboard')}
          className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 rounded flex items-center justify-center gap-1"
        >
          <BarChart3 className="w-4 h-4" />
          Dashboard
        </button>
      </div>
    </Screen>
  );

  const EntryScreen = () => (
    <Screen title="New Detail Entry">
      {/* Vehicle Info Form */}
      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">License Plate</label>
          <input 
            type="text" 
            placeholder="ABC-123"
            className="w-full p-3 border rounded-lg"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Stock Number <span className="text-gray-400">(optional)</span></label>
          <input 
            type="text" 
            placeholder="Stock #"
            className="w-full p-3 border rounded-lg"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Detail Type</label>
          <select className="w-full p-3 border rounded-lg bg-white">
            <option>Select type...</option>
            <option>New Vehicle Delivery</option>
            <option>CPO/Used Vehicle</option>
            <option>Customer Car</option>
            <option>Showroom Detail</option>
            <option>Demo Vehicle</option>
            <option>Other</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Detailer Name</label>
          <input 
            type="text" 
            placeholder="Detailer name"
            className="w-full p-3 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
          <select className="w-full p-3 border rounded-lg bg-white">
            <option>Select location...</option>
            <option>Bay 1</option>
            <option>Bay 2</option>
            <option>Bay 3</option>
            <option>Outside</option>
            <option>Service Lane</option>
            <option>Wash Bay</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Hours Listed</label>
          <input 
            type="number" 
            step="0.1"
            placeholder="2.5"
            className="w-full p-3 border rounded-lg"
          />
        </div>
      </div>

      {/* Preset Notes - Quick Select */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Quick Notes</label>
        <div className="grid grid-cols-2 gap-2 mb-2">
          {['Pet hair removal', 'Extra polish needed', 'Heavy cleaning required', 'Minor touch-up', 'Leather conditioning', 'Paint correction'].map(note => (
            <button
              key={note}
              className="text-xs bg-gray-100 hover:bg-blue-100 text-gray-700 p-2 rounded border text-left"
              onClick={() => setDraftEntry({...draftEntry, notes: (draftEntry.notes || '') + note + '. '})}
            >
              + {note}
            </button>
          ))}
        </div>
      </div>

      {/* Notes Section */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
        <textarea 
          placeholder="Additional details, issues, or special instructions..."
          rows="3"
          value={draftEntry.notes || ''}
          onChange={(e) => setDraftEntry({...draftEntry, notes: e.target.value})}
          className="w-full p-3 border rounded-lg resize-none"
        />
        {draftEntry.notes && (
          <div className="mt-1 text-xs text-green-600">✓ Draft auto-saved</div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        <button 
          onClick={() => setCurrentScreen('main')}
          className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 p-3 rounded-lg"
        >
          Cancel
        </button>
        <button className="flex-1 bg-blue-500 hover:bg-blue-600 text-white p-3 rounded-lg">
          Add Entry
        </button>
      </div>
    </Screen>
  );

  const LogScreen = () => (
    <Screen title="Complete Log">
      {/* Filter Controls */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <select className="p-2 border rounded-lg">
          <option>All Detailers</option>
          <option>John Smith</option>
          <option>Maria Garcia</option>
          <option>David Chen</option>
        </select>
        <select className="p-2 border rounded-lg">
          <option>Last 30 Days</option>
          <option>This Week</option>
          <option>This Month</option>
          <option>All Time</option>
        </select>
      </div>

      {/* Search */}
      <div className="mb-4">
        <input 
          type="text" 
          placeholder="Search by license plate, stock #, or notes..."
          className="w-full p-3 border rounded-lg"
        />
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-2 mb-4 text-center">
        <div className="bg-blue-50 p-2 rounded">
          <div className="font-bold text-blue-600">47</div>
          <div className="text-xs text-gray-600">Total Entries</div>
        </div>
        <div className="bg-green-50 p-2 rounded">
          <div className="font-bold text-green-600">89.5</div>
          <div className="text-xs text-gray-600">Total Hours</div>
        </div>
        <div className="bg-orange-50 p-2 rounded">
          <div className="font-bold text-orange-600">1.9</div>
          <div className="text-xs text-gray-600">Avg/Entry</div>
        </div>
      </div>

      {/* Bulk Selection */}
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center gap-2">
          <input 
            type="checkbox" 
            onChange={(e) => {
              if (e.target.checked) {
                setSelectedEntries([1,2,3,4,5]);
              } else {
                setSelectedEntries([]);
              }
            }}
            className="rounded"
          />
          <span className="text-sm text-gray-600">Select All</span>
          {selectedEntries.length > 0 && (
            <span className="text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded">
              {selectedEntries.length} selected
            </span>
          )}
        </div>
        {selectedEntries.length > 0 && (
          <button className="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600">
            Bulk Export
          </button>
        )}
      </div>

      {/* Log Entries - List View */}
      <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
        {[
          { id: 1, plate: 'ABC-123', stock: 'ST001', type: 'New Vehicle Delivery', detailer: 'John S.', hours: 2.5, date: '12/15', location: 'Bay 1', notes: 'Extra polish needed' },
          { id: 2, plate: 'XYZ-789', stock: '', type: 'Customer Car', detailer: 'Maria G.', hours: 1.8, date: '12/15', location: 'Bay 2', notes: 'Pet hair removal' },
          { id: 3, plate: 'DEF-456', stock: 'ST002', type: 'CPO/Used Vehicle', detailer: 'David C.', hours: 3.2, date: '12/14', location: 'Outside', notes: 'Heavy detailing required' },
          { id: 4, plate: 'GHI-101', stock: '', type: 'Demo Vehicle', detailer: 'John S.', hours: 1.2, date: '12/14', location: 'Bay 3', notes: '' },
          { id: 5, plate: 'JKL-202', stock: 'ST003', type: 'Showroom Detail', detailer: 'Maria G.', hours: 4.1, date: '12/13', location: 'Bay 1', notes: 'Quick touch-up' }
        ].map((entry, i) => (
          <div key={i} className="bg-white border rounded-lg p-3 shadow-sm">
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center gap-3">
                <input 
                  type="checkbox" 
                  checked={selectedEntries.includes(entry.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedEntries([...selectedEntries, entry.id]);
                    } else {
                      setSelectedEntries(selectedEntries.filter(id => id !== entry.id));
                    }
                  }}
                  className="rounded"
                />
                <div>
                  <div className="font-medium text-lg">{entry.plate}</div>
                  {entry.stock && <div className="text-sm text-gray-500">Stock: {entry.stock}</div>}
                </div>
              </div>
              <div className="text-right">
                <div className={`font-bold text-lg ${entry.hours > 3 ? 'text-red-600' : 'text-blue-600'}`}>
                  {entry.hours}h
                  {entry.hours > 3 && <span className="text-xs ml-1">⚠️</span>}
                </div>
                <div className="text-xs text-gray-500">{entry.date}</div>
                <button 
                  onClick={() => setEditingEntry(entry)}
                  className="text-xs text-blue-600 hover:underline"
                >
                  Quick Edit
                </button>
              </div>
            </div>
            <div className="text-sm text-gray-600 mb-1">
              <span className="font-medium">{entry.type}</span> • {entry.detailer} • {entry.location}
            </div>
            {entry.notes && (
              <div className="text-sm bg-gray-50 p-2 rounded italic">
                "{entry.notes}"
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button 
          onClick={() => setCurrentScreen('main')}
          className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 p-2 rounded"
        >
          Back
        </button>
        <button className="flex-1 bg-blue-500 hover:bg-blue-600 text-white p-2 rounded flex items-center justify-center gap-1">
          <Download className="w-4 h-4" />
          Export This View
        </button>
      </div>
    </Screen>
  );

  const DashboardScreen = () => (
    <Screen title="Weekly Dashboard">
      {/* Filter */}
      <div className="mb-4">
        <select className="w-full p-2 border rounded-lg">
          <option>This Week</option>
          <option>Last Week</option>
          <option>This Month</option>
        </select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">23</div>
          <div className="text-sm text-gray-600">Cars Completed</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-green-600">42.5</div>
          <div className="text-sm text-gray-600">Total Hours</div>
        </div>
        <div className="bg-orange-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">1.85</div>
          <div className="text-sm text-gray-600">Avg Hours/Car</div>
        </div>
        <div className="bg-red-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-red-600">2</div>
          <div className="text-sm text-gray-600">Overtime Days</div>
        </div>
      </div>

      {/* Detailer Performance */}
      <div className="mb-6">
        <h3 className="font-medium text-gray-700 mb-3">Detailer Performance</h3>
        <div className="space-y-2">
          <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
            <div>
              <div className="font-medium">John Smith</div>
              <div className="text-sm text-gray-600">8 cars • 15.2 hrs</div>
            </div>
            <div className="text-right">
              <div className="font-bold">1.9h</div>
              <div className="text-xs text-gray-500">avg/car</div>
            </div>
          </div>
          <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
            <div>
              <div className="font-medium">Maria Garcia</div>
              <div className="text-sm text-gray-600">10 cars • 18.5 hrs</div>
            </div>
            <div className="text-right">
              <div className="font-bold">1.85h</div>
              <div className="text-xs text-gray-500">avg/car</div>
            </div>
          </div>
          <div className="flex justify-between items-center p-3 bg-red-50 rounded border border-red-200">
            <div>
              <div className="font-medium">David Chen</div>
              <div className="text-sm text-gray-600">5 cars • 8.8 hrs</div>
              <div className="text-xs text-red-600">⚠️ Overtime yesterday</div>
            </div>
            <div className="text-right">
              <div className="font-bold">1.76h</div>
              <div className="text-xs text-gray-500">avg/car</div>
            </div>
          </div>
        </div>
      </div>

      <button 
        onClick={() => setCurrentScreen('main')}
        className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 p-3 rounded-lg"
      >
        Back to Main
      </button>
    </Screen>
  );

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Auto Detailing Time Tracker</h1>
          <p className="text-gray-600">Interactive Wireframe Prototype</p>
        </div>
        
        {currentScreen === 'main' && <MainScreen />}
        {currentScreen === 'entry' && <EntryScreen />}
        {currentScreen === 'log' && <LogScreen />}
        {currentScreen === 'dashboard' && <DashboardScreen />}
        
        <div className="mt-8 p-4 bg-white rounded-lg shadow">
          <h3 className="font-bold mb-2">Wireframe Navigation:</h3>
          <p className="text-sm text-gray-600">
            Click the screen buttons (Main/Entry/Log/Dashboard) to navigate between wireframes. 
            This prototype shows the core user flows and mobile-first design approach with all enhanced features.
          </p>
        </div>
      </div>
    </div>
  );
};

export default DetailingWireframes;